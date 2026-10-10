import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('roomly_analytics', Path(__file__).resolve().parents[1] / 'src/backend/analytics_lambda.py')
analytics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analytics)

class AnalyticsSecurityTests(unittest.TestCase):
    def event(self, issuer='https://issuer.example', subject='admin-sub'):
        return {'requestContext': {'authorizer': {'jwt': {'claims': {'iss': issuer, 'sub': subject}}}}}

    def invoke(self, event, users, configured=True):
        table = Mock()
        table.scan.return_value = {'Items': users}
        with patch.dict(os.environ, {'AUTH_ISSUER': 'https://issuer.example', 'USERS_TABLE': 'RoomlyUsers'} if configured else {}, clear=True), patch.object(analytics.boto3, 'resource') as resource, patch.object(analytics, 'read_text', return_value='{}') as read, patch.object(analytics, 'read_csv', return_value=[]):
            resource.return_value.Table.return_value = table
            response = analytics.lambda_handler(event, None)
            return response, read.called

    def user(self, **changes):
        return dict({'auth_issuer': 'https://issuer.example', 'auth_sub': 'admin-sub', 'is_active': True, 'is_admin': True}, **changes)

    def test_admin_can_read(self):
        response, read = self.invoke(self.event(), [self.user()])
        self.assertEqual(response['statusCode'], 200)
        self.assertTrue(read)

    def test_denied_requests_never_read_analytics(self):
        cases = [({}, [], True, 401), (self.event(issuer='wrong'), [], True, 401),
                 (self.event(), [self.user(is_admin=False)], True, 403),
                 (self.event(), [self.user(is_active=False)], True, 403),
                 (self.event(), [], True, 403),
                 (self.event(), [self.user(), self.user()], True, 403),
                 (self.event(), [self.user(is_admin='true')], True, 403),
                 (self.event(), [], False, 503)]
        for event, users, configured, status in cases:
            with self.subTest(status=status, users=users):
                response, read = self.invoke(event, users, configured)
                self.assertEqual(response['statusCode'], status)
                self.assertFalse(read)

    def test_pagination_finds_admin_on_later_page(self):
        table = Mock()
        table.scan.side_effect = [{'Items': [], 'LastEvaluatedKey': {'user_id': 'U001'}}, {'Items': [self.user()]}]
        with patch.dict(os.environ, {'AUTH_ISSUER': 'https://issuer.example', 'USERS_TABLE': 'RoomlyUsers'}), patch.object(analytics.boto3, 'resource') as resource:
            resource.return_value.Table.return_value = table
            self.assertIsNone(analytics.check_admin(self.event()))
            self.assertEqual(table.scan.call_count, 2)

if __name__ == '__main__':
    unittest.main()
