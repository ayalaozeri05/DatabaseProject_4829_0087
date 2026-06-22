// ─── Shared utilities for TransRoute Planner ─────────────────────────────────

// Toast notifications
const toastContainer = document.getElementById('toast-container');
function toast(msg, type = 'success') {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = (type === 'success' ? '✓ ' : '✕ ') + msg;
  toastContainer.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// API helper
async function api(url, method = 'GET', body = null) {
  const opts = { method, headers: {'Content-Type':'application/json'}, cache: 'no-store' };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || json.message || 'Server error');
  return json;
}

// Build an HTML table from array of objects
function buildTable(rows, columns, onRowClick) {
  if (!rows.length) return '<div class="no-data">No records found</div>';
  const heads = columns.map(c => `<th>${c.label}</th>`).join('');
  const body = rows.map((r, i) => {
    const cells = columns.map(c => `<td>${c.render ? c.render(r) : (r[c.key] ?? '—')}</td>`).join('');
    return `<tr data-idx="${i}">${cells}</tr>`;
  }).join('');
  return `<div class="table-wrap"><table><thead><tr>${heads}</tr></thead><tbody>${body}</tbody></table></div>`;
}

// Occupancy bar helper
function occBar(pct) {
  const p = parseFloat(pct) || 0;
  const col = p >= 100 ? '#e53e3e' : p >= 80 ? '#d97706' : '#22a06b';
  return `<div class="occ-bar"><div class="occ-track"><div class="occ-fill" style="width:${Math.min(p,100)}%;background:${col}"></div></div><span style="font-size:11px;font-weight:600;color:${col}">${p}%</span></div>`;
}

// Status badge helper
function statusBadge(s) {
  const map = {
    'Confirmed':  'badge-green',
    'Pending':    'badge-orange',
    'Cancelled':  'badge-red',
    'Waitlisted': 'badge-purple',
  };
  return `<span class="badge ${map[s] || 'badge-gray'}">${s || '—'}</span>`;
}

// Modal open/close
function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
// Close on overlay click
document.querySelectorAll('.modal-overlay').forEach(ov => {
  ov.addEventListener('click', e => { if (e.target === ov) ov.classList.remove('open'); });
});

// Populate select with options
function populateSelect(el, items, valKey, labelKey, empty = null) {
  el.innerHTML = '';
  if (empty !== null) el.innerHTML = `<option value="">${empty}</option>`;
  items.forEach(item => {
    const o = document.createElement('option');
    o.value = item[valKey];
    o.textContent = item[labelKey];
    el.appendChild(o);
  });
}

// Active nav link
const currentPath = window.location.pathname;
document.querySelectorAll('.nav-link').forEach(a => {
  if (a.getAttribute('href') === currentPath ||
      (currentPath !== '/' && a.getAttribute('href') !== '/' && currentPath.startsWith(a.getAttribute('href')))) {
    a.classList.add('active');
  }
});
