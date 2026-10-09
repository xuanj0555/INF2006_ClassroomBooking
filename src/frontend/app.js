const $ = s => document.querySelector(s);
const AWS_API = 'https://kw67yao8v7.execute-api.us-east-1.amazonaws.com';

let user = null;
let rooms = [];
let bookings = [];
let allBookings = [];
let availability = {};
let pending = null;
let people = [];
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let cancelId = null;
let toastTimer;

async function api(path, data = undefined, method = undefined) {
  const options = {
    method: method || (data !== undefined ? 'POST' : 'GET'),
    headers: {}
  };

  if (data !== undefined) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(data);
  }

  const accessToken = roomlyAuth.token();
  if (!accessToken) {
    if (!$('#login').open) $('#login').showModal();
    throw Error('Please sign in to continue.');
  }
  options.headers.Authorization = 'Bearer ' + accessToken;
  const response = await fetch(AWS_API + '/' + path, options);
  if (response.status === 401) {
    if (!$('#login').open) $('#login').showModal();
    throw Error('Your sign-in has expired or was rejected. Please sign in again.');
  }

  let value = {};
  try {
    value = await response.json();
  } catch (_) {
    value = {};
  }

  if (!response.ok) {
    throw Error(`${options.method} /${path.split('?')[0]} failed (${response.status}): ${value.message || 'Request failed'}`);
  }

  return value;
}

function toast(msg, error = false) {
  if (error && $('#login').open) { $('#loginError').textContent = msg; $('#loginError').hidden = false; }
  $('#toast').textContent = msg;
  $('#toast').className = error ? 'error' : '';
  $('#toast').style.display = 'block';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $('#toast').style.display = 'none', 5500);
}

const fmt = s => new Date(s).toLocaleString('en-SG', {
  timeZone: 'Asia/Singapore',
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit'
});

function view(v) {
  if (v === 'admin' && !user?.is_admin) return;
  if (v === 'admin') adminView('rooms');
  if (v === 'insights' && user?.role !== 'faculty') return;

  ['find', 'bookings', 'insights', 'admin'].forEach(x => {
    $('#' + x).hidden = x !== v;
  });

  document.querySelectorAll('.tab').forEach(b =>
    b.classList.toggle('active', b.dataset.view === v)
  );
}

async function refresh() {
  const roomData = await api('rooms');

if (!Array.isArray(roomData.rooms)) {
  throw new Error('AWS returned an unexpected room-list format.');
}
  const bookingData = await api('my-bookings');

  rooms = roomData.rooms || [];
  bookings = bookingData.bookings || [];
  allBookings = bookings;
  availability = {};

  if (user?.role === 'faculty') {
    const allBookingData = await api('all-bookings');
    allBookings = allBookingData.bookings || [];
  }

  const date = $('#date').value;

  const results = await Promise.all(
    rooms.map(room =>
      api(
        `availability?room_id=${encodeURIComponent(room.room_id)}&date=${encodeURIComponent(date)}`
      )
    )
  );

  results.forEach(result => {
    availability[result.room_id] = result.slots || [];
  });

  renderRooms();
  renderBookings();
}

function renderRooms() {
  const filtered = rooms.filter(
    room => room.capacity >= Number($('#capacity').value)
  );

  $('#roomCount').textContent = filtered.length + ' rooms';

  $('#rooms').innerHTML = filtered.map(room => {
    const slots = availability[room.room_id] || [];

    return `
      <article class="room">
        <div class="room-top">
          <span class="room-id">${esc(room.room_id)}</span>
          <span class="capacity">${room.capacity} people</span>
        </div>
        <div class="room-body">
          <h3>${esc(room.name)}</h3>
          <div class="location">${esc(room.location)}</div>
          <div class="slot-label">SELECT A START TIME · 1 HOUR</div>
          <div class="slots">
            ${slots.map(slot => `
              <button
                class="slot"
                data-room="${esc(room.room_id)}"
                data-start="${slot.start_time}"
                ${slot.available ? '' : 'disabled'}
                title="${slot.available ? 'Book this slot' : 'Already reserved or unavailable'}"
              >
                ${new Date(slot.start_time).toLocaleTimeString('en-SG', {
                  timeZone: 'Asia/Singapore',
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: false
                })}
              </button>
            `).join('')}
          </div>
        </div>
      </article>
    `;
  }).join('');

  document.querySelectorAll('.slot:not(:disabled)').forEach(button => {
    button.onclick = () => {
      const room = rooms.find(r => r.room_id === button.dataset.room);
      if (!room) return;

      pending = {
        room_id: button.dataset.room,
        start_time: button.dataset.start
      };

      $('#summary').textContent =
        `${esc(room.name)} · ${fmt(pending.start_time)} · 1 hour`;
      $('#participants').innerHTML = people.filter(p => p.user_id !== user.user_id).map(p => `<label class="check"><input type="checkbox" name="participant" value="${esc(p.user_id)}">${esc(p.name)}</label>`).join('');
      $('#confirm').showModal();
    };
  });
}

function bookingRoomName(booking) {
  return rooms.find(r => r.room_id === booking.room_id)?.name || booking.room_id;
}

function bookingAttendance(booking) {
  return booking.attendance?.outcome || 'pending';
}

function cards(list, staff = false) {
  if (!list.length) {
    return `
      <div class="empty">
        <h2>Your next session starts here.</h2>
        <p>No bookings yet. Choose a room and make some time for focused work.</p>
      </div>
    `;
  }

  return list.map(booking => {
    const dt = new Date(booking.start_time);
    const future = dt > new Date();
    const attendance = bookingAttendance(booking);

    const canCancel =
      booking.status === 'confirmed' &&
      future &&
      (booking.your_role === 'organiser' || user?.is_admin);

    const canCheckIn =
      booking.status === 'confirmed' &&
      (booking.participants || []).some(p => p.user_id === user?.user_id) &&
      attendance === 'pending' &&
      new Date() >= dt &&
      new Date() <= new Date(dt.getTime() + 900000);

    let badge = 'confirmed';
    if (booking.status === 'cancelled') badge = 'cancelled';
    else if (attendance === 'attended') badge = 'checked in';
    else if (attendance === 'no_show') badge = 'no-show';

    const participantText = staff
      ? `<p>Organiser: ${esc(booking.organiser_id)}</p>`
      : `<p>${booking.your_role === 'organiser' ? 'Organiser' : 'Participant'}</p>`;

    return `
      <article class="booking">
        <div class="detail">
          <h3>${esc(bookingRoomName(booking))}</h3>
          <p>${fmt(booking.start_time)} · 1 hour</p>
          <p>Reference ${esc(booking.booking_id)}</p>
          ${participantText}<p>Members: ${(booking.participants || []).map(p => esc(p.name)).join(', ')}</p>
        </div>
        <span class="badge">${badge}</span>
        ${canCancel ? `<button data-cancel="${esc(booking.booking_id)}">Cancel</button>` : ''}
        ${canCheckIn ? `<button data-check="${esc(booking.booking_id)}">Check in</button>` : ''}
      </article>
    `;
  }).join('');
}

function renderBookings() {
  const upcoming = bookings.filter(
    booking =>
      booking.status === 'confirmed' &&
      new Date(booking.start_time) > new Date()
  );

  $('#count').textContent = upcoming.length;
  $('#bookingList').innerHTML = cards(bookings);

  if (user.role === 'faculty') {
    $('#staffList').innerHTML = cards(allBookings, true);

    const active = allBookings.filter(b => b.status === 'confirmed');

    $('#metrics').innerHTML = [
      ['All confirmed bookings', active.length],
      ['Checked in', active.filter(b => bookingAttendance(b) === 'attended').length],
      ['Recorded no-shows', active.filter(b => bookingAttendance(b) === 'no_show').length]
    ].map(([label, value]) =>
      `<div class="metric">${label}<strong>${value}</strong></div>`
    ).join('');
  }

  document.querySelectorAll('[data-cancel]').forEach(button => {
    button.onclick = () => {
      cancelId = button.dataset.cancel;
      $('#cancelDialog').showModal();
    };
  });

  document.querySelectorAll('[data-check]').forEach(button => {
    button.onclick = async () => {
      try {
        const result = await api(
          `bookings/${encodeURIComponent(button.dataset.check)}/check-in`,
          {},
          'POST'
        );
        toast(result.message || 'Check-in successful.');
        await refresh();
      } catch (error) {
        toast(error.message, true);
      }
    };
  });
}

async function init() {
  await roomlyAuth.callback();
  if (!roomlyAuth.token()) {
    $('#login').showModal();
    return;
  }
  const session = await api('session');
  user = session.user;
  if (!user) throw Error('Your sign-in account is not linked to a Roomly user.');
  if (!$('#date').value) $('#date').value = session.today;
  $('#date').min = session.today;
  $('#identity').replaceChildren();
  const name = document.createElement('span');
  name.textContent = user.name;
  const button = document.createElement('button');
  button.textContent = 'Sign out';
  button.onclick = () => roomlyAuth.signOut();
  $('#identity').append(name, button);
  $('#staffTab').hidden = user.role !== 'faculty';
  $('#adminTab').hidden = !user.is_admin;
  people = (await api('users')).users;
  await refresh();
}

$('#login').addEventListener('cancel', e => e.preventDefault());
$('#loginForm').onsubmit = async e => {
  e.preventDefault();
  const button = $('#loginSubmit');
  $('#loginError').hidden = true;
  button.disabled = true;
  button.textContent = 'Opening sign-in…';
  try {
    if (!window.roomlyAuth) throw Error('Sign-in could not load. Restart the server and reload this page.');
    await roomlyAuth.signIn();
  } catch (error) {
    toast(error.message, true);
    button.disabled = false;
    button.textContent = 'Sign in';
  }
};


$('#confirmForm').onsubmit = async e => {
  e.preventDefault();
  $('#bookButton').disabled = true;

  try {
    const participant_ids = [...document.querySelectorAll('[name=participant]:checked')].map(x => x.value);
    const result = await api('bookings', {...pending, participant_ids});
    $('#confirm').close();
    toast(result.message || 'Booking confirmed.');
    await refresh();
    view('bookings');
  } catch (error) {
    toast(error.message, true);
    await refresh();
  } finally {
    $('#bookButton').disabled = false;
  }
};

$('#back').onclick = () => $('#confirm').close();
$('#keep').onclick = () => $('#cancelDialog').close();

$('#doCancel').onclick = async () => {
  try {
    const result = await api(
      `bookings/${encodeURIComponent(cancelId)}`,
      undefined,
      'DELETE'
    );
    $('#cancelDialog').close();
    toast(result.message || 'Booking cancelled.');
    await refresh();
  } catch (error) {
    toast(error.message, true);
  }
};

document.querySelectorAll('.tab').forEach(button => {
  button.onclick = () => view(button.dataset.view);
});

$('#date').onchange = () => {
  if ($('#date').value) {
    refresh().catch(error => toast(error.message, true));
  }
};

$('#capacity').onchange = renderRooms;

init().catch(error => {
  // A data-loading failure must not turn a signed-in user into a signed-out user.
  if (!roomlyAuth.token() && !$('#login').open) $('#login').showModal();
  toast(error.message, true);
  if (!$('#login').open) {
    let notice = document.getElementById('startupError');
    if (!notice) {
      notice = document.createElement('p');
      notice.id = 'startupError';
      notice.setAttribute('role', 'alert');
      document.querySelector('main').prepend(notice);
    }
    notice.textContent = 'Roomly could not finish loading. ' + error.message + ' Reload after the API configuration is corrected.';
  }
});

let adminRooms = [];
function adminView(v) {
  ['rooms', 'analytics', 'forecast'].forEach(x => $('#admin-' + x).hidden = x !== v);
  document.querySelectorAll('.subtab').forEach(b => b.classList.toggle('active', b.dataset.admin === v));
  (v === 'rooms' ? loadAdminRooms() : loadAnalytics(v)).catch(e => toast(e.message, true));
}
function resetRoomForm() {
  $('#roomForm').reset(); $('#roomId').value = ''; $('#roomId').readOnly = true; delete $('#roomForm').dataset.editingId; $('#roomCancel').hidden = true;
  $('#roomSubmit').textContent = 'Add room';
}
async function loadAdminRooms() {
  adminRooms = (await api('admin/rooms')).rooms;
  $('#roomList').innerHTML = adminRooms.map(r => `<article class="booking"><div class="detail"><h3>${esc(r.room_id)} · ${esc(r.name)}</h3><p>${esc(r.location)} · ${r.capacity} people · ${r.is_active ? 'Active' : 'Inactive'}</p></div><button data-edit="${esc(r.room_id)}">Edit</button></article>`).join('');
  document.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => {
    const r = adminRooms.find(r => r.room_id === b.dataset.edit);
    $('#roomForm').dataset.editingId = r.room_id; $('#roomId').readOnly = true; $('#roomId').value = r.room_id; $('#roomName').value = r.name;
    $('#roomLocation').value = r.location; $('#roomCapacity').value = r.capacity;
    $('#roomActive').checked = !!r.is_active;
    $('#roomCancel').hidden = false; $('#roomSubmit').textContent = 'Save changes';
  });
}
function chart(title, rows, label) {
  const max = Math.max(1, ...rows.map(r => r.count));
  return `<section class="note"><h3>${esc(title)}</h3>${rows.map(r => `<p>${esc(label(r))} — ${r.count} reservations<br><meter min="0" max="${max}" value="${r.count}" style="width:100%"></meter></p>`).join('')}</section>`;
}
async function loadAnalytics(v) {
  if (v === 'forecast') {
    const body = $('#forecastBody');
    body.textContent = 'Loading historical demand patterns from AWS…';
    try {
      const d = await api('analytics');
      if (!d.summary || !Array.isArray(d.by_room) ||
          !Array.isArray(d.by_weekday) || !Array.isArray(d.by_start_hour)) {
        throw Error('Unexpected analytics response format');
      }
      const rank = (rows, field) => rows.map(r => ({
        label: String(r[field]), count: Number(r.reservation_count)
      })).sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
      const rooms = rank(d.by_room, 'room_id');
      const days = rank(d.by_weekday, 'weekday');
      const hours = rank(d.by_start_hour, 'start_hour');
      if ([...rooms, ...days, ...hours].some(r => !Number.isFinite(r.count) || r.count < 0)) {
        throw Error('Invalid historical reservation counts');
      }
      const hourLabel = r => `${String(r.label).padStart(2, '0')}:00`;
      const highlights = [
        ['Busiest historical room', rooms[0]?.label ?? 'No data'],
        ['Busiest weekday', days[0]?.label ?? 'No data'],
        ['Busiest start hour', hours[0] ? hourLabel(hours[0]) : 'No data']
      ];
      body.innerHTML =
        `<p>Historical patterns from AWS · ${esc(d.summary.record_count)} reservations · ` +
        `${esc(d.summary.coverage_start)} to ${esc(d.summary.coverage_end)}</p>` +
        `<div class="metrics">` + highlights.map(([label, value]) =>
          `<div class="metric">${esc(label)}<strong>${esc(value)}</strong></div>`
        ).join('') + `</div>` +
        chart('Most reserved historical rooms', rooms.slice(0, 10), r => r.label) +
        chart('Weekdays ranked by reservation count', days, r => r.label) +
        chart('Start hours ranked by reservation count', hours, hourLabel) +
        `<p>Rankings use recorded reservation counts, not occupancy rates or attendance. ` +
        `Tied counts share the same rank; the cards show one of the tied entries. ` +
        `Weekday and hour totals are separate summaries and cannot identify a busiest weekday–hour combination. ` +
        `Use these patterns to review historical scheduling and room demand. ` +
        `They are not predictions or live availability for the four demo rooms.</p>`;
    } catch (error) {
      body.textContent = `Could not load demand patterns: ${error.message}`;
      throw error;
    }
    return;
  }

  const body = $('#analyticsBody');
  $('#analyticsSource').textContent = 'Loading historical analytics…';
  body.textContent = 'Loading results from AWS…';

  try {
    const d = await api('analytics');

    if (
      !d.summary ||
      !Array.isArray(d.by_room) ||
      !Array.isArray(d.by_weekday) ||
      !Array.isArray(d.by_start_hour)
    ) {
      throw new Error('Unexpected analytics response format');
    }

    const s = d.summary;

    // Adapt AWS fields to the existing chart helper.
    const rooms = d.by_room.map(r => ({
      room_id: r.room_id,
      count: r.reservation_count
    })).sort((a, b) => b.count - a.count);

    const weekdays = d.by_weekday.map(r => ({
      weekday: r.weekday,
      count: r.reservation_count
    }));

    const hours = d.by_start_hour.map(r => ({
      hour: r.start_hour,
      count: r.reservation_count
    }));

    const weekendCount = weekdays
      .filter(r => ['Saturday', 'Sunday'].includes(r.weekday))
      .reduce((sum, r) => sum + r.count, 0);

    const weekendShare = s.record_count
      ? Math.round(weekendCount / s.record_count * 100)
      : 0;

    $('#analyticsSource').textContent =
      'Historical analytics from AWS · separate from live bookings';

    const metrics = [
      ['Reserved hours', s.total_reserved_hours],
      ['Average minutes', s.average_duration_minutes],
      ['Weekend share', `${weekendShare}%`]
    ];

    body.innerHTML =
      `<p>${esc(String(s.record_count))} reservations · ` +
      `${esc(s.coverage_start)} to ${esc(s.coverage_end)}</p>` +
      `<div class="metrics">` +
      metrics.map(([label, value]) =>
        `<div class="metric">${esc(label)}` +
        `<strong>${esc(String(value))}</strong></div>`
      ).join('') +
      `</div>` +
      chart('Top historical rooms', rooms.slice(0, 12), r => r.room_id) +
      chart('By weekday', weekdays, r => r.weekday) +
      chart('By hour', hours, r => `${r.hour}:00`) +
      `<p>Historical reservation counts can inform room planning. ` +
      `They do not prove attendance or predict demand for the current ` +
      `demo rooms.</p>`;
  } catch (error) {
    $('#analyticsSource').textContent = 'AWS analytics unavailable';
    body.textContent = `Could not load analytics: ${error.message}`;
    throw error;
  }
}
document.querySelectorAll('.subtab').forEach(b => b.onclick = () => adminView(b.dataset.admin));
$('#roomCancel').onclick = resetRoomForm;
$('#roomForm').onsubmit = async e => {
  e.preventDefault();
  const editingId = $('#roomForm').dataset.editingId;
  const room_id = editingId;
  try {
    await api('admin/rooms/' + (editingId ? 'update' : 'create'), {
      room_id, name: $('#roomName').value, capacity: Number($('#roomCapacity').value),
      location: $('#roomLocation').value, is_active: $('#roomActive').checked
    });
    resetRoomForm(); await loadAdminRooms(); await refresh(); toast('Room saved.');
  } catch (e) { toast(e.message, true); }
};