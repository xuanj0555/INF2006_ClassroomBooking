import sys, tempfile, unittest
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/backend'))
from adminService import RoomlyService
from bookingService import SG
from API import dispatch

class AdminIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'db.sqlite3'
        self.csv=Path(self.tmp.name)/'history.csv'
        self.csv.write_text('start_time,end_time,duration_minutes,room_id,reservation_date,weekday,start_hour,month,is_weekend\n2024-01-06 10:00,2024-01-06 11:00,60,H1,2024-01-06,Saturday,10,1,TRUE\n2024-01-08 10:00,2024-01-08 12:00,120,H2,2024-01-08,Monday,10,1,FALSE\n')
        self.s=RoomlyService(self.path,lambda:datetime(2026,9,28,tzinfo=SG),self.csv)
    def tearDown(self): self.tmp.cleanup()
    def call(self,uid,path,body=None): return dispatch(self.s,'GET' if body is None else 'POST',path,{},body,uid)
    def test_permissions(self):
        for uid,status in [(None,401),('U001',403),('U004',403),('U005',200)]:
            self.assertEqual(self.call(uid,'/admin/rooms')[0],status)
    def test_history_is_separate_and_idempotent(self):
        d=self.call('U005','/admin/analytics/reservations')[1]
        self.assertEqual((d['total'],d['reserved_hours'],d['avg_duration_minutes'],d['weekend_share']),(2,3,90,0.5))
        self.assertEqual(self.s.my_bookings('U001')['bookings'],[])
        self.assertNotIn('H1',[r['room_id'] for r in self.s.list_rooms()['rooms']])
        again=RoomlyService(self.path,history_csv=self.csv)
        self.assertEqual(again.reservation_analytics('U005')['total'],2)
    def test_room_management_and_capacity(self):
        data=dict(name='Test',location='Campus',capacity=3,amenities='Board',is_active=True)
        status,r=self.call('U005','/admin/rooms/create',data)
        self.assertEqual(status,201)
        rid=r['room_id']
        self.assertEqual(dispatch(self.s,'POST','/bookings',{},dict(room_id=rid,start_time='2026-10-01T10:00:00+08:00',participant_ids=['U002']),'U001')[0],201)
        self.assertEqual(self.call('U005','/admin/rooms/update',dict(data,room_id=rid,capacity=1))[0],409)
        self.assertEqual(self.call('U005','/admin/rooms/update',dict(data,room_id=rid,is_active=False))[0],200)
        self.assertNotIn(rid,[r['room_id'] for r in self.s.list_rooms()['rooms']])
        self.assertEqual(self.call('U005','/admin/rooms/create',dict(data,capacity='3'))[0],400)
