"""Small in-memory DynamoDB mock used by the cloud-backend tests.

It implements only the DynamoDB operations used by DynamoDBService. The goal is
not to replace DynamoDB, but to make the service-level tests repeatable without
AWS credentials or a live table. Transactions are protected by a lock and are
applied atomically after all conditions pass.
"""
from copy import deepcopy
from threading import RLock
from types import SimpleNamespace

from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer

DESER = TypeDeserializer()


class FakeTable:
    def __init__(self, resource, name):
        self.resource = resource
        self.name = name

    def get_item(self, Key, ConsistentRead=True):
        item = self.resource._get(self.name, Key)
        return {"Item": deepcopy(item)} if item is not None else {}

    def scan(self, **kwargs):
        return {"Items": deepcopy(list(self.resource._tables[self.name].values()))}

    def query(self, **kwargs):
        values = kwargs.get("ExpressionAttributeValues", {})
        rid = DESER.deserialize(values.get(":r")) if ":r" in values else None
        prefix = DESER.deserialize(values.get(":day")) if ":day" in values else None
        rows = []
        for item in self.resource._tables[self.name].values():
            if rid is not None and item.get("resource_id") != rid:
                continue
            if prefix is not None and not item.get("slot_start", "").startswith(prefix):
                continue
            rows.append(deepcopy(item))
        return {"Items": rows}


class FakeDynamoResource:
    def __init__(self):
        self._tables = {
            "Rooms": {},
            "RoomlyUsers": {},
            "RoomlyBookings": {},
            "RoomlyReservations": {},
        }
        self._lock = RLock()
        meta_client = SimpleNamespace(meta=SimpleNamespace(region_name="us-east-1", endpoint_url="http://mock"))
        self.meta = SimpleNamespace(client=meta_client)
        self.client = FakeDynamoClient(self)

    def Table(self, name):
        if name not in self._tables:
            raise KeyError(name)
        return FakeTable(self, name)

    def seed(self, table, item):
        key = self._key(table, item)
        self._tables[table][key] = deepcopy(item)

    @staticmethod
    def _key(table, item):
        if table == "RoomlyReservations":
            return item["resource_id"], item["slot_start"]
        field = {
            "Rooms": "room_id",
            "RoomlyUsers": "user_id",
            "RoomlyBookings": "booking_id",
        }[table]
        return item[field]

    def _get(self, table, key):
        if table == "RoomlyReservations":
            k = (key["resource_id"], key["slot_start"])
        else:
            field = {
                "Rooms": "room_id",
                "RoomlyUsers": "user_id",
                "RoomlyBookings": "booking_id",
            }[table]
            k = key[field]
        return self._tables[table].get(k)

    def _condition_error(self):
        return ClientError(
            {
                "Error": {
                    "Code": "TransactionCanceledException",
                    "Message": "Transaction cancelled",
                },
                "CancellationReasons": [{"Code": "ConditionalCheckFailed"}],
            },
            "TransactWriteItems",
        )


class FakeDynamoClient:
    def __init__(self, resource):
        self.resource = resource
        self.meta = resource.meta.client.meta

    def transact_write_items(self, TransactItems):
        with self.resource._lock:
            snapshot = deepcopy(self.resource._tables)
            try:
                for action in TransactItems:
                    self._check_action(snapshot, action)
                for action in TransactItems:
                    self._apply_action(snapshot, action)
            except _ConditionFailed:
                raise self.resource._condition_error()
            self.resource._tables = snapshot
            return {}

    def _table(self, snapshot, name):
        return snapshot[name]

    def _get(self, snapshot, table_name, key):
        if table_name == "RoomlyReservations":
            k = (key["resource_id"], key["slot_start"])
        else:
            field = {
                "Rooms": "room_id",
                "RoomlyUsers": "user_id",
                "RoomlyBookings": "booking_id",
            }[table_name]
            k = key[field]
        return snapshot[table_name].get(k)

    def _check_action(self, snapshot, action):
        if "Put" in action:
            p = action["Put"]
            item = {k: DESER.deserialize(v) for k, v in p["Item"].items()}
            old = self._get(snapshot, p["TableName"], item)
            if not self._condition(p.get("ConditionExpression"), old, p.get("ExpressionAttributeNames", {}), p.get("ExpressionAttributeValues", {})):
                raise _ConditionFailed
        elif "ConditionCheck" in action:
            c = action["ConditionCheck"]
            old = self._get(snapshot, c["TableName"], {k: DESER.deserialize(v) for k, v in c["Key"].items()})
            if not self._condition(c.get("ConditionExpression"), old, c.get("ExpressionAttributeNames", {}), c.get("ExpressionAttributeValues", {})):
                raise _ConditionFailed
        elif "Update" in action:
            u = action["Update"]
            old = self._get(snapshot, u["TableName"], {k: DESER.deserialize(v) for k, v in u["Key"].items()})
            if not self._condition(u.get("ConditionExpression"), old, u.get("ExpressionAttributeNames", {}), u.get("ExpressionAttributeValues", {})):
                raise _ConditionFailed
        elif "Delete" in action:
            d = action["Delete"]
            old = self._get(snapshot, d["TableName"], {k: DESER.deserialize(v) for k, v in d["Key"].items()})
            if not self._condition(d.get("ConditionExpression"), old, d.get("ExpressionAttributeNames", {}), d.get("ExpressionAttributeValues", {})):
                raise _ConditionFailed

    def _apply_action(self, snapshot, action):
        if "Put" in action:
            p = action["Put"]
            item = {k: DESER.deserialize(v) for k, v in p["Item"].items()}
            snapshot[p["TableName"]][self._key_from_item(p["TableName"], item)] = item
        elif "Update" in action:
            u = action["Update"]
            key = {k: DESER.deserialize(v) for k, v in u["Key"].items()}
            table = snapshot[u["TableName"]]
            current = deepcopy(self._get(snapshot, u["TableName"], key))
            expr_names = u.get("ExpressionAttributeNames", {})
            values = {k: DESER.deserialize(v) for k, v in u.get("ExpressionAttributeValues", {}).items()}
            update = u["UpdateExpression"]
            if update.startswith("SET "):
                for assignment in update[4:].split(","):
                    field, token = [x.strip() for x in assignment.split("=", 1)]
                    field = expr_names.get(field, field)
                    current[field] = values[token]
            table[self._key_from_item(u["TableName"], current)] = current
        elif "Delete" in action:
            d = action["Delete"]
            key = {k: DESER.deserialize(v) for k, v in d["Key"].items()}
            table = snapshot[d["TableName"]]
            table.pop(self._key_from_item(d["TableName"], key), None)

    @staticmethod
    def _key_from_item(table, item):
        if table == "RoomlyReservations":
            return item["resource_id"], item["slot_start"]
        field = {
            "Rooms": "room_id",
            "RoomlyUsers": "user_id",
            "RoomlyBookings": "booking_id",
        }[table]
        return item[field]

    @staticmethod
    def _condition(expression, item, names, raw_values):
        if not expression:
            return True
        if item is None:
            item = {}
        values = {k: DESER.deserialize(v) for k, v in raw_values.items()}
        expression = expression.replace("#cap", "capacity").replace("#st", "status")
        for part in [p.strip() for p in expression.split(" AND ")]:
            if part.startswith("attribute_not_exists("):
                field = part[len("attribute_not_exists("):-1]
                if field in item:
                    return False
            elif part.startswith("attribute_exists("):
                field = part[len("attribute_exists("):-1]
                if field not in item:
                    return False
            elif ">=" in part:
                field, token = [x.strip() for x in part.split(">=", 1)]
                if field not in item or item[field] < values[token]:
                    return False
            elif "=" in part:
                field, token = [x.strip() for x in part.split("=", 1)]
                if field not in item or item[field] != values[token]:
                    return False
            else:
                raise AssertionError(f"Unsupported mock condition: {part}")
        return True


class _ConditionFailed(Exception):
    pass
