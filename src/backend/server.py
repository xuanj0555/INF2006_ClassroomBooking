"""Local teaching prototype. Demo identity selection is NOT production authentication."""
import json, sqlite3, secrets, os, csv
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
USERS={'student-a':('Alex Tan','student'),'student-b':('Jamie Lim','student'),'staff':('Morgan Lee','staff'),'admin':('Riley Chen','admin')}
SEED_ROOMS=[('R001','Study Room A',4,'Level 2 · Quiet wing','Whiteboard,Power outlets'),('R002','Study Room B',6,'Level 2 · Learning commons','Display,Whiteboard'),('R003','Study Room C',8,'Level 3 · Collaboration zone','Display,Power outlets'),('R004','Study Room D',4,'Level 3 · Quiet wing','Whiteboard,Power outlets')]
def conn():
 c=sqlite3.connect(DB,timeout=10);c.row_factory=sqlite3.Row;return c
HISTORY_CSV=ROOT/'data/reservations_cleaned_newversion.csv'
CAPACITY_CSV=ROOT/'data/room_capacity.csv'  # capacity per room_id, supplied separately from the reservation history
def room_sort_key(rid):return (0,int(rid)) if rid.isdigit() else (1,rid)
with conn() as c:
 c.executescript('CREATE TABLE IF NOT EXISTS bookings(id TEXT PRIMARY KEY,user TEXT,room TEXT,start TEXT,status TEXT,attendance TEXT,created TEXT); CREATE UNIQUE INDEX IF NOT EXISTS slot ON bookings(room,start) WHERE status="confirmed"; CREATE TABLE IF NOT EXISTS rooms(id TEXT PRIMARY KEY,name TEXT,capacity INTEGER,location TEXT,amenities TEXT,active INTEGER DEFAULT 1); CREATE TABLE IF NOT EXISTS reservations_history(start_time TEXT,end_time TEXT,duration_minutes INTEGER,room_id TEXT,reservation_date TEXT,weekday TEXT,start_hour INTEGER,month INTEGER,is_weekend INTEGER);')
 if not c.execute('SELECT 1 FROM reservations_history LIMIT 1').fetchone() and HISTORY_CSV.exists():
  with open(HISTORY_CSV,newline='') as f:
   pos=f.tell();first=f.readline()
   f.seek(pos if first.startswith('start_time') else f.tell())  # skip a stray title line above the real header, if present
   reader=csv.DictReader(f)
   batch=[(r['start_time'],r['end_time'],int(r['duration_minutes']),r['room_id'],r['reservation_date'],r['weekday'],int(r['start_hour']),int(r['month']),1 if r['is_weekend'].strip().upper()=='TRUE' else 0) for r in reader]
  c.executemany('INSERT INTO reservations_history VALUES(?,?,?,?,?,?,?,?,?)',batch)
 if not c.execute('SELECT 1 FROM rooms LIMIT 1').fetchone():
  csv_ids=sorted({r[0] for r in c.execute('SELECT DISTINCT room_id FROM reservations_history')},key=room_sort_key)
  if csv_ids:
   capacity={}
   if CAPACITY_CSV.exists():
    with open(CAPACITY_CSV,newline='') as f:
     capacity={r['room_id']:int(r['capacity']) for r in csv.DictReader(f)}
   busiest=set(r['room_id'] for r in c.execute('SELECT room_id,COUNT(*) n FROM reservations_history GROUP BY room_id ORDER BY n DESC LIMIT 12'))
   seed=[]
   for rid in csv_ids:
    cap=capacity.get(rid,0)
    live=cap>0 and rid in busiest
    if cap>0:loc='Among the 12 busiest rooms in the historical log — edit in Admin' if live else 'Not among the 12 busiest rooms — inactive by default, edit in Admin to activate'
    else:loc='Capacity not provided by source data — set one before activating'
    seed.append((rid,f'Room {rid}',cap,loc,'',1 if live else 0))
  else:
   seed=[(r[0],r[1],r[2],r[3],r[4],1) for r in SEED_ROOMS]
  c.executemany('INSERT INTO rooms VALUES(?,?,?,?,?,?)',seed)
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
  if p.path=='/api/rooms':
   with conn() as c:return self.send(200,[dict(r) for r in c.execute('SELECT id,name,capacity,location,amenities FROM rooms WHERE active=1 ORDER BY id')])
  if p.path=='/api/admin/rooms':
   if USERS[u][1]!='admin':return self.send(403,{'message':'Admin access required.'})
   with conn() as c:return self.send(200,[dict(r) for r in c.execute('SELECT * FROM rooms ORDER BY id')])
  if p.path=='/api/admin/analytics/reservations':
   if USERS[u][1]!='admin':return self.send(403,{'message':'Admin access required.'})
   with conn() as c:
    total=c.execute('SELECT COUNT(*) FROM reservations_history').fetchone()[0]
    if not total:return self.send(200,{'source':'reservations_cleaned_newversion.csv (sample historical data)','total':0})
    date_from,date_to=c.execute('SELECT MIN(reservation_date),MAX(reservation_date) FROM reservations_history').fetchone()
    by_room=[dict(r) for r in c.execute('SELECT room_id,COUNT(*) count FROM reservations_history GROUP BY room_id ORDER BY count DESC LIMIT 12')]
    order="CASE weekday WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 ELSE 7 END"
    by_weekday=[dict(r) for r in c.execute(f'SELECT weekday,COUNT(*) count FROM reservations_history GROUP BY weekday ORDER BY {order}')]
    by_hour=[dict(r) for r in c.execute('SELECT start_hour hour,COUNT(*) count FROM reservations_history GROUP BY start_hour ORDER BY hour')]
    by_month=[dict(r) for r in c.execute('SELECT month,COUNT(*) count FROM reservations_history GROUP BY month ORDER BY month')]
    avg_dur,weekend_n=c.execute('SELECT AVG(duration_minutes),SUM(is_weekend) FROM reservations_history').fetchone()
    return self.send(200,{'source':'reservations_cleaned_newversion.csv (sample historical data)','total':total,'date_from':date_from,'date_to':date_to,'by_room':by_room,'by_weekday':by_weekday,'by_hour':by_hour,'by_month':by_month,'avg_duration_minutes':round(avg_dur,1),'weekend_share':round(weekend_n/total,3)})
  if p.path=='/api/admin/analytics/forecast':
   if USERS[u][1]!='admin':return self.send(403,{'message':'Admin access required.'})
   with conn() as c:
    total=c.execute('SELECT COUNT(*) FROM reservations_history').fetchone()[0]
    if not total:return self.send(200,{'method':'naive historical average (not a trained or validated model)','total_samples':0})
    weeks=c.execute('SELECT (JULIANDAY(MAX(reservation_date))-JULIANDAY(MIN(reservation_date)))/7.0 FROM reservations_history').fetchone()[0] or 1
    order="CASE weekday WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 ELSE 7 END"
    busiest_slots=[dict(r) for r in c.execute(f'SELECT weekday,start_hour hour,COUNT(*) count,ROUND(COUNT(*)/?,2) expected_per_week FROM reservations_history GROUP BY weekday,start_hour ORDER BY count DESC LIMIT 10',(weeks,))]
    likely_busiest_rooms=[dict(r) for r in c.execute('SELECT room_id,COUNT(*) count,ROUND(COUNT(*)/?,2) expected_per_week FROM reservations_history GROUP BY room_id ORDER BY count DESC LIMIT 8',(weeks,))]
    return self.send(200,{'method':'naive historical average (not a trained or validated model) — projects next week from last year of logs','total_samples':total,'weeks_of_history':round(weeks,1),'busiest_slots':busiest_slots,'likely_busiest_rooms':likely_busiest_rooms})
  with conn() as c:
   c.execute('UPDATE bookings SET attendance="no_show" WHERE status="confirmed" AND attendance="pending" AND start < ?',((now()-timedelta(minutes=15)).isoformat(),))
   rows=[dict(r) for r in c.execute('SELECT * FROM bookings ORDER BY start')]
  if p.path=='/api/availability':
   date=parse_qs(p.query).get('date',[''])[0]
   return self.send(200,[{'room':r['room'],'start':r['start']} for r in rows if r['status']=='confirmed' and r['start'].startswith(date)])
  if p.path=='/api/bookings':return self.send(200,rows if USERS[u][1] in ('staff','admin') else [r for r in rows if r['user']==u])
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
  if self.path in ('/api/admin/rooms/create','/api/admin/rooms/update'):
   if USERS[u][1]!='admin':return self.send(403,{'message':'Admin access required.'})
   name=(body.get('name') or '').strip();location=(body.get('location') or '').strip();amenities=(body.get('amenities') or '').strip()
   try:capacity=int(body.get('capacity'))
   except (TypeError,ValueError):return self.send(400,{'message':'Capacity must be a number.'})
   if not name or not location or capacity<1:return self.send(400,{'message':'Enter a name, location and a capacity of at least 1.'})
   active=1 if body.get('active',True) else 0
   with conn() as c:
    if self.path=='/api/admin/rooms/create':
     last=c.execute("SELECT id FROM rooms WHERE id LIKE 'R%' ORDER BY id DESC LIMIT 1").fetchone()
     rid=f'R{(int(last["id"][1:])+1 if last else 1):03d}'
     c.execute('INSERT INTO rooms VALUES(?,?,?,?,?,?)',(rid,name,capacity,location,amenities,active))
     return self.send(200,{'id':rid,'message':'Room added.'})
    rid=body.get('id')
    if not c.execute('SELECT 1 FROM rooms WHERE id=?',(rid,)).fetchone():return self.send(404,{'message':'Room not found.'})
    c.execute('UPDATE rooms SET name=?,capacity=?,location=?,amenities=?,active=? WHERE id=?',(name,capacity,location,amenities,active,rid))
    return self.send(200,{'message':'Room updated.'})
  try:
   with conn() as c:
    c.execute('BEGIN IMMEDIATE')
    if self.path=='/api/bookings':
     room=body.get('room');start=body.get('start')
     try:dt=datetime.fromisoformat(start)
     except (TypeError,ValueError):return self.send(400,{'message':'Select a valid date and time.'})
     if dt.tzinfo is None:return self.send(400,{'message':'Timezone required.'})
     dt=dt.astimezone(SG);start=dt.isoformat()
     active_rooms=[r['id'] for r in c.execute('SELECT id FROM rooms WHERE active=1')]
     if room not in active_rooms or dt.minute or dt.second or dt.microsecond or not 9<=dt.hour<18 or dt<=now():return self.send(400,{'message':'Choose a future one-hour slot between 09:00 and 18:00.'})
     count=c.execute('SELECT COUNT(*) FROM bookings WHERE user=? AND status="confirmed" AND start>?',(u,now().isoformat())).fetchone()[0]
     if count>=2:return self.send(409,{'message':'You already have two upcoming bookings. Cancel one first.'})
     bid=secrets.token_hex(4).upper();c.execute('INSERT INTO bookings VALUES(?,?,?,?,?,?,?)',(bid,u,room,start,'confirmed','pending',now().isoformat()))
     result={'id':bid,'message':'Your room is booked.'}
    elif self.path in ['/api/cancel','/api/check-in']:
     r=c.execute('SELECT * FROM bookings WHERE id=?',(body.get('id'),)).fetchone()
     if not r:return self.send(404,{'message':'Booking not found.'})
     if r['user']!=u and USERS[u][1] not in ('staff','admin'):return self.send(403,{'message':'You cannot change another student’s booking.'})
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
