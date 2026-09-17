import os,tempfile,importlib.util,threading,json,urllib.request,urllib.error,http.cookiejar,unittest
from pathlib import Path
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
fd,db=tempfile.mkstemp();os.close(fd);os.environ['BOOKING_DB']=db
spec=importlib.util.spec_from_file_location('server',Path(__file__).resolve().parents[1]/'src/backend/server.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
server=s.ThreadingHTTPServer(('127.0.0.1',0),s.Handler);threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}'
def client(user):
 o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()));call(o,'demo-login',{'user':user});return o
def call(o,path,data=None):
 req=urllib.request.Request(base+'/api/'+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
 try:
  with o.open(req) as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:return e.code,json.load(e)
class Test(unittest.TestCase):
 def setUp(self):
  with s.conn() as c:c.execute('DELETE FROM bookings')
  self.a=client('student-a');self.b=client('student-b');self.start=(s.now()+timedelta(days=1)).replace(hour=10,minute=0,second=0,microsecond=0).isoformat()
 def test_booking_ownership_cancel(self):
  status,r=call(self.a,'bookings',{'room':'R001','start':self.start});self.assertEqual(status,200)
  self.assertEqual(call(self.b,'cancel',{'id':r['id']})[0],403)
  self.assertEqual(call(self.a,'cancel',{'id':r['id']})[0],200)
  self.assertEqual(call(self.b,'bookings',{'room':'R001','start':self.start})[0],200)
 def test_competing_requests(self):
  with ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda o:call(o,'bookings',{'room':'R002','start':self.start})[0],[self.a,self.b]))
  self.assertEqual(sorted(results),[200,409])
 def test_limits_auth_and_checkin(self):
  self.assertEqual(call(urllib.request.build_opener(),'bookings')[0],401)
  for room in ['R001','R002']:self.assertEqual(call(self.a,'bookings',{'room':room,'start':self.start})[0],200)
  self.assertEqual(call(self.a,'bookings',{'room':'R003','start':self.start})[0],409)
  rows=call(self.a,'bookings')[1];self.assertEqual(call(self.a,'check-in',{'id':rows[0]['id']})[0],409)
 def test_attendance_and_persistence(self):
  start=s.now().replace(minute=0,second=0,microsecond=0)
  with s.conn() as c:c.execute('INSERT INTO bookings VALUES(?,?,?,?,?,?,?)',('CHECK','student-a','R001',start.isoformat(),'confirmed','pending',s.now().isoformat()))
  original=s.now;s.now=lambda:start+timedelta(minutes=5)
  try:self.assertEqual(call(self.a,'check-in',{'id':'CHECK'})[0],200)
  finally:s.now=original
  with s.conn() as c:self.assertEqual(c.execute('SELECT attendance FROM bookings WHERE id="CHECK"').fetchone()[0],'attended')
if __name__=='__main__':
 try:unittest.main(exit=False)
 finally:server.shutdown();os.unlink(db)
