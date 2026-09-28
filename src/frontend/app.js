const $ = s => document.querySelector(s);

let user = null;
let rooms = [];
let bookings = [];
let allBookings = [];
let availability = {};
let pending = null;
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

  const response = await fetch('/api/' + path, options);

  let value = {};
  try {
    value = await response.json();
  } catch (_) {
    value = {};
  }

  if (!response.ok) {
    throw Error(value.message || 'Request failed');
  }

  return value;
}

function toast(msg, error = false) {
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
  if (v === 'insights' && user?.role !== 'faculty') return;

  ['find', 'bookings', 'insights'].forEach(x => {
    $('#' + x).hidden = x !== v;
  });

  document.querySelectorAll('.tab').forEach(b =>
    b.classList.toggle('active', b.dataset.view === v)
  );
}

async function refresh() {
  const roomData = await api('rooms');
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
          <span class="room-id">${room.room_id}</span>
          <span class="capacity">${room.capacity} people</span>
        </div>
        <div class="room-body">
          <h3>${room.name}</h3>
          <div class="location">${room.location}</div>
          <div class="slot-label">SELECT A START TIME · 1 HOUR</div>
          <div class="slots">
            ${slots.map(slot => `
              <button
                class="slot"
                data-room="${room.room_id}"
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
        `${room.name} · ${fmt(pending.start_time)} · 1 hour`;
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
      attendance === 'pending' &&
      new Date() >= dt &&
      new Date() <= new Date(dt.getTime() + 900000);

    let badge = 'confirmed';
    if (booking.status === 'cancelled') badge = 'cancelled';
    else if (attendance === 'attended') badge = 'checked in';
    else if (attendance === 'no_show') badge = 'no-show';

    const participantText = staff
      ? `<p>Organiser: ${booking.organiser_id}</p>`
      : `<p>${booking.your_role === 'organiser' ? 'Organiser' : 'Participant'}</p>`;

    return `
      <article class="booking">
        <div class="detail">
          <h3>${bookingRoomName(booking)}</h3>
          <p>${fmt(booking.start_time)} · 1 hour</p>
          <p>Reference ${booking.booking_id}</p>
          ${participantText}
        </div>
        <span class="badge">${badge}</span>
        ${canCancel ? `<button data-cancel="${booking.booking_id}">Cancel</button>` : ''}
        ${canCheckIn ? `<button data-check="${booking.booking_id}">Check in</button>` : ''}
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
  const session = await api('session');
  user = session.user;

  if (!$('#date').value) $('#date').value = session.today;
  $('#date').min = session.today;

  if (!user) {
    $('#login').showModal();
    return;
  }

  $('#identity').replaceChildren();

  const name = document.createElement('span');
  name.textContent = user.name;

  const button = document.createElement('button');
  button.textContent = 'Switch account';
  button.onclick = async () => {
    await api('logout', {});
    location.reload();
  };

  $('#identity').append(name, button);
  $('#staffTab').hidden = user.role !== 'faculty';

  await refresh();
}

$('#login').addEventListener('cancel', e => e.preventDefault());

$('#loginForm').onsubmit = async e => {
  e.preventDefault();

  try {
    await api('demo-login', {
      user_id: $('#account').value
    });
    $('#login').close();
    await init();
  } catch (error) {
    toast(error.message, true);
  }
};

$('#confirmForm').onsubmit = async e => {
  e.preventDefault();
  $('#bookButton').disabled = true;

  try {
    const result = await api('bookings', pending);
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

init().catch(error => toast(error.message, true));
