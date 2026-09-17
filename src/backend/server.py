"""Local teaching prototype. Demo identity selection is NOT production authentication."""
import json, sqlite3, secrets, os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from http.cookies import SimpleCookie
from urllib.parse import urlparse, parse_qs
ROOT=Path(__file__).resolve().parents[2]
WEB=ROOT/'src/frontend'
DB=Path(os.environ.get('BOOKING_DB', str(ROOT/'bookings.sqlite3')))
SG=timezone(timedelta(hours=8))
SESSIONS={}
USERS={'student-a':('Alex Tan','student'),'student-b':('Jamie Lim','student'),'staff':('Morgan Lee','staff')}
ROOMS=[('R001','Study Room A',4,'Level 2 · Quiet wing','Whiteboard,Power outlets'),('R002','Study Room B',6,'Level 2 · Learning commons','Display,Whiteboard'),('R003','Study Room C',8,'Level 3 · Collaboration zone','Display,Power outlets'),('R004','Study Room D',4,'Level 3 · Quiet wing','Whiteboard,Power outlets')]
def conn():
 c=sqlite3.connect(DB,timeout=10);c.row_factory=sqlite3.Row;return c
with conn() as c:
 c.executescript('CREATE TABLE IF NOT EXISTS bookings(id TEXT PRIMARY KEY,user TEXT,room TEXT,start TEXT,status TEXT,attendance TEXT,created TEXT); CREATE UNIQUE INDEX IF NOT EXISTS slot ON bookings(room,start) WHERE status="confirmed";')
def now():return datetime.now(SG)
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(WEB),**kw)
 def send(self,status,data,cookie=None):
  raw=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)))
  if cookie:self.send_header('Set-Cookie',cookie)
  self.end_headers();self.wfile.write(raw)
 def user(self):
  cookie=SimpleCookie();cookie.load(self.headers.get('Cookie',''));token=cookie.get('session');return SESSIONS.get(token.value) if token else None
 def do_GET(self):
  p=urlparse(self.path)
  if not p.path.startswith('/api/'):
   if p.path not in ['/', '/index.html','/app.js','/style.css','/favicon.svg']:return self.send_error(404)
   return super().do_GET()
  u=self.user()
  if p.path=='/api/session':return self.send(200,{'user':{'id':u,'name':USERS[u][0],'role':USERS[u][1]} if u else None,'today':now().date().isoformat()})
  if not u:return self.send(401,{'message':'Choose a demo account to continue.'})
  if p.path=='/api/rooms':return self.send(200,[dict(zip(['id','name','capacity','location','amenities'],r)) for r in ROOMS])
  with conn() as c:
   c.execute('UPDATE bookings SET attendance="no_show" WHERE status="confirmed" AND attendance="pending" AND start < ?',((now()-timedelta(minutes=15)).isoformat(),))
   rows=[dict(r) for r in c.execute('SELECT * FROM bookings ORDER BY start')]
  if p.path=='/api/availability':
   date=parse_qs(p.query).get('date',[''])[0]
   return self.send(200,[{'room':r['room'],'start':r['start']} for r in rows if r['status']=='confirmed' and r['start'].startswith(date)])
  if p.path=='/api/bookings':return self.send(200,rows if USERS[u][1]=='staff' else [r for r in rows if r['user']==u])
  return self.send(404,{'message':'Not found'})
 def do_POST(self):
  origin=self.headers.get('Origin')
  if origin and origin!=f'http://{self.headers.get("Host")}':return self.send(403,{'message':'Request origin rejected.'})
  try:
   n=int(self.headers.get('Content-Length',0))
   if n>10000:raise ValueError()
   body=json.loads(self.rfile.read(n) or '{}')
   if not isinstance(body,dict):raise ValueError()
  except (ValueError,TypeError):return self.send(400,{'message':'Invalid request.'})
  if self.path=='/api/demo-login':
   u=body.get('user')
   if u not in USERS:return self.send(400,{'message':'Unknown demo account.'})
   t=secrets.token_urlsafe(32);SESSIONS[t]=u
   return self.send(200,{'ok':True},f'session={t}; HttpOnly; SameSite=Strict; Path=/')
  u=self.user()
  if not u:return self.send(401,{'message':'Please select a demo account.'})
  if self.path=='/api/logout':
   ck=SimpleCookie();ck.load(self.headers.get('Cookie',''));SESSIONS.pop(ck['session'].value,None)
   return self.send(200,{'ok':True},'session=; Max-Age=0; HttpOnly; SameSite=Strict; Path=/')
  try:
   with conn() as c:
    c.execute('BEGIN IMMEDIATE')
    if self.path=='/api/bookings':
     room=body.get('room');start=body.get('start')
     try:dt=datetime.fromisoformat(start)
     except (TypeError,ValueError):return self.send(400,{'message':'Select a valid date and time.'})
     if dt.tzinfo is None:return self.send(400,{'message':'Timezone required.'})
     dt=dt.astimezone(SG);start=dt.isoformat()
     if room not in [r[0] for r in ROOMS] or dt.minute or dt.second or dt.microsecond or not 9<=dt.hour<18 or dt<=now():return self.send(400,{'message':'Choose a future one-hour slot between 09:00 and 18:00.'})
     count=c.execute('SELECT COUNT(*) FROM bookings WHERE user=? AND status="confirmed" AND start>?',(u,now().isoformat())).fetchone()[0]
     if count>=2:return self.send(409,{'message':'You already have two upcoming bookings. Cancel one first.'})
     bid=secrets.token_hex(4).upper();c.execute('INSERT INTO bookings VALUES(?,?,?,?,?,?,?)',(bid,u,room,start,'confirmed','pending',now().isoformat()))
     result={'id':bid,'message':'Your room is booked.'}
    elif self.path in ['/api/cancel','/api/check-in']:
     r=c.execute('SELECT * FROM bookings WHERE id=?',(body.get('id'),)).fetchone()
     if not r:return self.send(404,{'message':'Booking not found.'})
     if r['user']!=u and USERS[u][1]!='staff':return self.send(403,{'message':'You cannot change another student’s booking.'})
     dt=datetime.fromisoformat(r['start'])
     if r['status']!='confirmed':return self.send(409,{'message':'This booking is no longer active.'})
     if self.path=='/api/cancel':
      if dt<=now():return self.send(409,{'message':'Only future bookings can be cancelled.'})
      c.execute('UPDATE bookings SET status="cancelled",attendance="not_applicable" WHERE id=?',(r['id'],));result={'message':'Booking cancelled. The slot is available again.'}
     else:
      if not dt<=now()<=dt+timedelta(minutes=15):return self.send(409,{'message':'Check-in opens at the start time and closes 15 minutes later.'})
      if r['attendance']=='attended':return self.send(409,{'message':'Already checked in.'})
      c.execute('UPDATE bookings SET attendance="attended" WHERE id=?',(r['id'],));result={'message':'You’re checked in. Enjoy your session!'}
    else:return self.send(404,{'message':'Not found.'})
   return self.send(200,result)
  except sqlite3.IntegrityError:return self.send(409,{'message':'That slot was just booked. Please choose another.'})
if __name__=='__main__':
 print('Open http://127.0.0.1:8765 — local demo only',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
