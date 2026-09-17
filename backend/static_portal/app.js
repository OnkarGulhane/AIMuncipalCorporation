// =============================================================================
// AI Municipal Corporation — Interactive Web Portal Controller
// =============================================================================

const API_BASE = '/api/v1';

// Pre-seeded Demo Role Accounts
const DEMO_ROLES = {
  requester: {
    email: 'citizen@demo.city.gov',
    password: 'Password123',
    name: 'Rahul Deshmukh',
    roleTag: 'CITIZEN',
    avatar: 'RD'
  },
  operator: {
    email: 'operator@demo.city.gov',
    password: 'Password123',
    name: 'Sanjay Field Operator',
    roleTag: 'FIELD OPERATOR',
    avatar: 'SO'
  },
  team_lead: {
    email: 'teamlead@demo.city.gov',
    password: 'Password123',
    name: 'Anjali Lead Engineer',
    roleTag: 'TEAM LEAD',
    avatar: 'AL'
  },
  manager: {
    email: 'manager@demo.city.gov',
    password: 'Password123',
    name: 'Vikas Ward Commissioner',
    roleTag: 'WARD MANAGER',
    avatar: 'VM'
  },
  administrator: {
    email: 'admin@demo.city.gov',
    password: 'Password123',
    name: 'Chief Municipal Administrator',
    roleTag: 'ADMINISTRATOR',
    avatar: 'HQ'
  }
};

let currentRole = 'manager';
let authToken = '';
let currentOpenCaseId = null;
let searchDebounceTimeout = null;

// =============================================================================
// INITIALIZATION
// =============================================================================
document.addEventListener('DOMContentLoaded', async () => {
  await switchRole('manager');
});

// =============================================================================
// AUTHENTICATION & ROLE SWITCHING
// =============================================================================
async function switchRole(roleKey) {
  currentRole = roleKey;
  const config = DEMO_ROLES[roleKey];
  if (!config) return;

  // Update Top Profile Badge
  document.getElementById('user-avatar').innerText = config.avatar;
  document.getElementById('user-name').innerText = config.name;
  document.getElementById('user-role-tag').innerText = config.roleTag;
  document.getElementById('role-select').value = roleKey;

  // Authenticate and fetch JWT token
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: config.email, password: config.password })
    });

    if (res.ok) {
      const data = await res.json();
      authToken = data.access_token;
      localStorage.setItem('auth_token', authToken);

      // Refresh currently active tab
      loadCurrentTab();
    } else {
      console.error('Login failed for role:', roleKey);
    }
  } catch (err) {
    console.error('Error during role authentication:', err);
  }
}

function getAuthHeaders() {
  return {
    'Authorization': `Bearer ${authToken}`,
    'Content-Type': 'application/json'
  };
}

// =============================================================================
// TAB NAVIGATION
// =============================================================================
function showTab(tabId) {
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

  const targetPane = document.getElementById(`tab-${tabId}`);
  const targetNav = document.getElementById(`nav-${tabId}`);

  if (targetPane) targetPane.classList.add('active');
  if (targetNav) targetNav.classList.add('active');

  loadCurrentTab();
}

function loadCurrentTab() {
  const activePane = document.querySelector('.tab-pane.active');
  if (!activePane) return;

  const id = activePane.id;
  if (id === 'tab-dashboard') loadDashboardData();
  else if (id === 'tab-cases') loadCases();
  else if (id === 'tab-escalations') loadEscalations();
  else if (id === 'tab-audit') loadAuditLogs();
  else if (id === 'tab-notifications') loadNotifications();
}

// =============================================================================
// 1. DASHBOARD & ANALYTICS
// =============================================================================
async function loadDashboardData() {
  try {
    const res = await fetch(`${API_BASE}/analytics/manager`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById('kpi-total').innerText = data.total_cases || 0;
    document.getElementById('kpi-active').innerText = data.active_cases || 0;
    document.getElementById('kpi-sla').innerText = `${data.sla_compliance_percent || 100}%`;
    document.getElementById('kpi-resolved').innerText = data.resolved_cases || 0;

    // Render AI Operational Insights
    const insightsList = document.getElementById('ai-insights-list');
    insightsList.innerHTML = '';
    if (data.ai_operational_insights && data.ai_operational_insights.length > 0) {
      data.ai_operational_insights.forEach(item => {
        insightsList.innerHTML += `
          <div class="ai-box" style="margin: 6px 0;">
            <div class="ai-box-header">
              <span>💡 ${item.title}</span>
              <span class="badge badge-${item.severity}">${item.severity.toUpperCase()}</span>
            </div>
            <div style="font-size: 12px; color: #CBD5E1;">${item.description}</div>
            <div style="font-size: 11px; color: #94A3B8; margin-top: 4px;"><strong>Action:</strong> ${item.recommendation}</div>
          </div>
        `;
      });
    } else {
      insightsList.innerHTML = '<div style="color: #64748B; font-size: 13px;">All municipal operations running within healthy SLA boundaries.</div>';
    }

    // Render Ward Performance Table
    const wardTbody = document.getElementById('ward-metrics-body');
    wardTbody.innerHTML = '';
    if (data.ward_metrics && data.ward_metrics.length > 0) {
      data.ward_metrics.forEach(w => {
        wardTbody.innerHTML += `
          <tr>
            <td><strong>${w.ward}</strong></td>
            <td>${w.total_cases}</td>
            <td><span class="badge badge-assigned">${w.active_cases}</span></td>
            <td>${w.top_category || 'Road Repairs'}</td>
            <td><span class="badge badge-${w.high_risk_cases > 0 ? 'high' : 'low'}">${w.high_risk_cases > 0 ? 'AT RISK' : 'HEALTHY'}</span></td>
          </tr>
        `;
      });
    } else {
      wardTbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #64748B;">No ward metrics reported yet.</td></tr>';
    }
  } catch (err) {
    console.error('Error loading dashboard analytics:', err);
  }
}

// =============================================================================
// 2. CASES LISTING & SEARCH
// =============================================================================
function debounceSearch() {
  clearTimeout(searchDebounceTimeout);
  searchDebounceTimeout = setTimeout(loadCases, 300);
}

async function loadCases() {
  try {
    const search = document.getElementById('case-search-input').value;
    const status = document.getElementById('case-filter-status').value;

    let url = `${API_BASE}/cases?size=50`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (status) url += `&status=${encodeURIComponent(status)}`;

    const res = await fetch(url, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const data = await res.json();

    const tbody = document.getElementById('cases-table-body');
    tbody.innerHTML = '';

    if (!data.items || data.items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #64748B; padding: 24px;">No matching cases found.</td></tr>';
      return;
    }

    data.items.forEach(c => {
      tbody.innerHTML += `
        <tr>
          <td><span class="case-detail-num" style="cursor: pointer;" onclick="openCaseDetail(${c.id})">${c.case_number}</span></td>
          <td>
            <div style="font-weight: 600; color: #F8FAFC;">${c.title}</div>
            <div style="font-size: 11px; color: #94A3B8; margin-top: 2px;">${c.description.substring(0, 60)}...</div>
          </td>
          <td>
            <div>${c.ward || 'Ward 12'}</div>
            <div style="font-size: 10px; color: #64748B;">${c.landmark || ''}</div>
          </td>
          <td><span class="badge badge-${c.priority}">${c.priority.toUpperCase()}</span></td>
          <td><span class="badge badge-${c.status}">${c.status.replace('_', ' ').toUpperCase()}</span></td>
          <td><span style="font-size: 11px; color: #38BDF8;">24h Target</span></td>
          <td>
            <button class="btn btn-outline btn-sm" onclick="openCaseDetail(${c.id})">View Detail</button>
          </td>
        </tr>
      `;
    });
  } catch (err) {
    console.error('Error loading cases:', err);
  }
}

// =============================================================================
// 3. CASE DETAIL & UNIFIED TIMELINE
// =============================================================================
async function openCaseDetail(caseId) {
  currentOpenCaseId = caseId;
  openModal('modal-case-detail');

  try {
    // 1. Fetch case details
    const caseRes = await fetch(`${API_BASE}/cases/${caseId}`, { headers: getAuthHeaders() });
    if (caseRes.ok) {
      const c = await caseRes.json();
      document.getElementById('detail-case-number').innerText = c.case_number;
      document.getElementById('detail-case-title').innerText = c.title;
      document.getElementById('detail-desc-text').innerText = c.description;
      document.getElementById('detail-location-text').innerText = `${c.ward} | ${c.landmark || ''} (${c.address || ''})`;

      const statusPill = document.getElementById('detail-status-pill');
      statusPill.className = `badge badge-${c.status}`;
      statusPill.innerText = c.status.replace('_', ' ').toUpperCase();

      renderRoleActions(c);
    }

    // 2. Fetch AI Analysis
    const aiRes = await fetch(`${API_BASE}/cases/${caseId}/ai-analysis`, { headers: getAuthHeaders() });
    if (aiRes.ok) {
      const ai = await aiRes.json();
      document.getElementById('detail-ai-confidence').innerText = `${Math.round(ai.confidence_score * 100)}% CONFIDENCE`;
      document.getElementById('detail-ai-cat').innerText = ai.suggested_category_name || 'Public Works';
      document.getElementById('detail-ai-action').innerText = ai.recommended_action || 'Assign to squad';
    }

    // 3. Fetch Unified Timeline
    loadCaseTimeline(caseId);
  } catch (err) {
    console.error('Error loading case detail:', err);
  }
}

async function loadCaseTimeline(caseId) {
  try {
    const res = await fetch(`${API_BASE}/cases/${caseId}/timeline`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const data = await res.json();

    const stream = document.getElementById('detail-timeline-stream');
    stream.innerHTML = '';

    if (!data.timeline || data.timeline.length === 0) {
      stream.innerHTML = '<div style="color: #64748B; font-size: 12px;">No activity recorded yet.</div>';
      return;
    }

    data.timeline.forEach(item => {
      const timeStr = new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      stream.innerHTML += `
        <div class="timeline-card">
          <div class="timeline-card-header">
            <span class="timeline-actor">${item.actor_name || 'System / AI'} <span style="font-size: 10px; color: #38BDF8;">(${item.actor_role || item.event_type})</span></span>
            <span class="timeline-time">${timeStr}</span>
          </div>
          <div class="timeline-text"><strong>${item.title}:</strong> ${item.description}</div>
        </div>
      `;
    });
  } catch (err) {
    console.error('Error loading timeline:', err);
  }
}

function renderRoleActions(caseObj) {
  const panel = document.getElementById('detail-actions-panel');
  panel.innerHTML = '';

  if (currentRole === 'requester') {
    if (caseObj.status === 'resolution_proposed') {
      panel.innerHTML = `
        <button class="btn btn-primary btn-sm" onclick="confirmResolution(${caseObj.id})" style="width: 100%; margin-bottom: 6px;">
          ✅ Confirm & Close Grievance
        </button>
        <button class="btn btn-outline btn-sm" onclick="rejectResolution(${caseObj.id})" style="width: 100%; color: #EF4444;">
          ❌ Reject & Reopen Complaint
        </button>
      `;
    }
  } else if (currentRole === 'operator') {
    if (caseObj.status === 'reported') {
      panel.innerHTML = `
        <button class="btn btn-primary btn-sm" onclick="claimCase(${caseObj.id})" style="width: 100%;">
          👷 Take Ownership & Claim Case
        </button>
      `;
    } else if (caseObj.status === 'assigned' || caseObj.status === 'investigated') {
      panel.innerHTML = `
        <button class="btn btn-primary btn-sm" onclick="proposeResolution(${caseObj.id})" style="width: 100%; margin-bottom: 6px;">
          ✨ Propose Field Resolution
        </button>
        <button class="btn btn-outline btn-sm" onclick="requestClarification(${caseObj.id})" style="width: 100%;">
          ❓ Request Info from Citizen
        </button>
      `;
    }
  } else if (currentRole === 'team_lead' || currentRole === 'manager') {
    panel.innerHTML = `
      <button class="btn btn-secondary btn-sm" onclick="manualEscalateCase(${caseObj.id})" style="width: 100%;">
        ⚠️ Trigger SLA Escalation
      </button>
    `;
  }
}

// Case Action Handlers
async function confirmResolution(caseId) {
  const notes = prompt('Enter citizen feedback (e.g., Verified on site, road repaired):', 'Inspected and verified. Road surface is smooth and safe now.');
  if (notes === null) return;

  const res = await fetch(`${API_BASE}/cases/${caseId}/confirm-resolution`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ notes })
  });
  if (res.ok) {
    alert('Resolution confirmed! Case successfully closed.');
    openCaseDetail(caseId);
    loadCases();
  }
}

async function rejectResolution(caseId) {
  const reason = prompt('Enter reason for rejecting resolution:', 'Issue still persists and requires further repair.');
  if (!reason) return;

  const res = await fetch(`${API_BASE}/cases/${caseId}/reject-resolution`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ rejection_reason: reason })
  });
  if (res.ok) {
    alert('Case rejected and reopened for inspection.');
    openCaseDetail(caseId);
    loadCases();
  }
}

async function claimCase(caseId) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/assignment`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ reason: 'Claimed by field squad operator' })
  });
  if (res.ok) {
    alert('Case claimed successfully!');
    openCaseDetail(caseId);
    loadCases();
  }
}

async function proposeResolution(caseId) {
  const notes = prompt('Enter field repair notes:', 'Pothole filled with hot-mix asphalt and compacted level with road.');
  if (!notes) return;

  const res = await fetch(`${API_BASE}/cases/${caseId}/status`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ new_status: 'resolution_proposed', resolution_notes: notes })
  });
  if (res.ok) {
    alert('Resolution proposed to citizen!');
    openCaseDetail(caseId);
    loadCases();
  }
}

async function requestClarification(caseId) {
  const query = prompt('Enter question for citizen:', 'Could you provide the exact electrical pole number near the crater?');
  if (!query) return;

  await fetch(`${API_BASE}/cases/${caseId}/status`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ new_status: 'waiting_info', reason: query })
  });
  await fetch(`${API_BASE}/cases/${caseId}/messages`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ message: query, message_type: 'query' })
  });
  alert('Clarification request sent to citizen!');
  openCaseDetail(caseId);
  loadCases();
}

async function manualEscalateCase(caseId) {
  const reason = prompt('Enter escalation reason:', 'Equipment repair delayed, requires emergency fleet dispatch.');
  if (!reason) return;

  const res = await fetch(`${API_BASE}/cases/${caseId}/escalations`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ reason, trigger_type: 'operator_request' })
  });
  if (res.ok) {
    alert('Escalation created!');
    openCaseDetail(caseId);
    loadCases();
  }
}

async function runAiTriageForCurrentCase() {
  if (!currentOpenCaseId) return;
  const res = await fetch(`${API_BASE}/cases/${currentOpenCaseId}/ai-analysis`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (res.ok) {
    openCaseDetail(currentOpenCaseId);
  }
}

async function handleSendMessage(e) {
  e.preventDefault();
  const input = document.getElementById('chat-input');
  const message = input.value.trim();
  if (!message || !currentOpenCaseId) return;

  const res = await fetch(`${API_BASE}/cases/${currentOpenCaseId}/messages`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ message, message_type: 'general' })
  });

  if (res.ok) {
    input.value = '';
    loadCaseTimeline(currentOpenCaseId);
  }
}

// =============================================================================
// 4. REPORT NEW GRIEVANCE
// =============================================================================
async function handleCreateCase(e) {
  e.preventDefault();
  const title = document.getElementById('case-in-title').value;
  const description = document.getElementById('case-in-description').value;
  const ward = document.getElementById('case-in-ward').value;
  const landmark = document.getElementById('case-in-landmark').value;
  const priority = document.getElementById('case-in-priority').value;
  const severity = document.getElementById('case-in-severity').value;

  try {
    const res = await fetch(`${API_BASE}/cases`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        title,
        description,
        ward,
        landmark,
        priority,
        severity
      })
    });

    if (res.ok) {
      const created = await res.json();
      closeModal('modal-new-case');
      document.getElementById('new-case-form').reset();
      alert(`Complaint registered successfully! Case Number: ${created.case_number}`);
      loadCases();
    } else {
      const err = await res.json();
      alert(`Error creating complaint: ${err.detail || 'Validation error'}`);
    }
  } catch (err) {
    console.error('Error registering complaint:', err);
  }
}

// =============================================================================
// 5. ESCALATIONS, AUDIT & NOTIFICATIONS
// =============================================================================
async function loadEscalations() {
  try {
    const res = await fetch(`${API_BASE}/escalations`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const list = await res.json();

    const tbody = document.getElementById('escalations-table-body');
    tbody.innerHTML = '';

    document.getElementById('escalations-count').innerText = list.length;

    if (list.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #64748B;">No active escalations.</td></tr>';
      return;
    }

    list.forEach(e => {
      tbody.innerHTML += `
        <tr>
          <td>#ESC-${e.id}</td>
          <td><span class="case-detail-num" style="cursor: pointer;" onclick="openCaseDetail(${e.case_id})">#${e.case_id}</span></td>
          <td>${e.reason}</td>
          <td><span class="badge badge-escalated">${e.trigger_type}</span></td>
          <td><span class="badge badge-${e.status}">${e.status.toUpperCase()}</span></td>
          <td>${new Date(e.created_at).toLocaleDateString()}</td>
          <td>
            ${e.status !== 'resolved' ? `<button class="btn btn-primary btn-sm" onclick="resolveEscalation(${e.case_id}, ${e.id})">Resolve</button>` : '<span style="color: #10B981;">Resolved</span>'}
          </td>
        </tr>
      `;
    });
  } catch (err) {
    console.error('Error loading escalations:', err);
  }
}

async function resolveEscalation(caseId, escalationId) {
  const notes = prompt('Enter escalation resolution notes:', 'Authorized emergency depot materials dispatch.');
  if (!notes) return;

  const res = await fetch(`${API_BASE}/cases/${caseId}/escalations/${escalationId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify({ status: 'resolved', resolution_notes: notes })
  });
  if (res.ok) {
    alert('Escalation marked as resolved!');
    loadEscalations();
  }
}

async function loadAuditLogs() {
  try {
    const res = await fetch(`${API_BASE}/admin/audit-logs`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const logs = await res.json();

    const tbody = document.getElementById('audit-table-body');
    tbody.innerHTML = '';

    if (logs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #64748B;">No audit history found.</td></tr>';
      return;
    }

    logs.forEach(l => {
      tbody.innerHTML += `
        <tr>
          <td style="font-size: 11px; color: #94A3B8;">${new Date(l.created_at).toLocaleString()}</td>
          <td>User #${l.actor_id || 'System'}</td>
          <td><strong>${l.action}</strong></td>
          <td><span class="badge">${l.resource_type} #${l.resource_id}</span></td>
          <td style="font-size: 12px;">${l.details || ''}</td>
          <td>${l.is_ai_action ? '<span class="badge badge-ai">AI ENGINE</span>' : '<span style="color: #64748B;">Human</span>'}</td>
        </tr>
      `;
    });
  } catch (err) {
    console.error('Error loading audit logs:', err);
  }
}

async function loadNotifications() {
  try {
    const res = await fetch(`${API_BASE}/notifications`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const items = await res.json();

    const list = document.getElementById('notifications-list');
    list.innerHTML = '';

    document.getElementById('notifications-count').innerText = items.filter(n => !n.is_read).length;

    if (items.length === 0) {
      list.innerHTML = '<div style="text-align: center; color: #64748B; padding: 24px;">No notifications.</div>';
      return;
    }

    items.forEach(n => {
      list.innerHTML += `
        <div class="timeline-card" style="margin-bottom: 8px; border-left: 3px solid ${n.is_read ? 'transparent' : '#3B82F6'};">
          <div class="timeline-card-header">
            <span class="timeline-actor">${n.title}</span>
            <span class="timeline-time">${new Date(n.created_at).toLocaleTimeString()}</span>
          </div>
          <div class="timeline-text">${n.message}</div>
        </div>
      `;
    });
  } catch (err) {
    console.error('Error loading notifications:', err);
  }
}

async function markAllNotificationsRead() {
  await fetch(`${API_BASE}/notifications/read-all`, {
    method: 'PATCH',
    headers: getAuthHeaders()
  });
  loadNotifications();
}

async function triggerSlaSweep() {
  const res = await fetch(`${API_BASE}/automation/sweep-slas-and-risks`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (res.ok) {
    alert('SLA and Risk background sweep completed across all active municipal cases!');
    loadDashboardData();
    loadCases();
  }
}

// =============================================================================
// MODAL CONTROLS
// =============================================================================
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('open');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('open');
}

function openNewCaseModal() {
  openModal('modal-new-case');
}
