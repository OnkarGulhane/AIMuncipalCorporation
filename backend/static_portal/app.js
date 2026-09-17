// =============================================================================
// AI Municipal Corporation — Interactive Web Portal Controller
// =============================================================================

const API_BASE = '/api/v1';

// Pre-seeded Demo Role Accounts
const DEMO_ROLES = {
  requester: {
    email: 'citizen@demo.com',
    password: 'Demo@1234',
    name: 'Aarav Sharma',
    roleTag: 'CITIZEN',
    avatar: 'AS'
  },
  operator: {
    email: 'operator@demo.com',
    password: 'Demo@1234',
    name: 'Rohan Deshmukh',
    roleTag: 'FIELD OPERATOR',
    avatar: 'RD'
  },
  team_lead: {
    email: 'teamlead@demo.com',
    password: 'Demo@1234',
    name: 'Priya Patil',
    roleTag: 'TEAM LEAD',
    avatar: 'PP'
  },
  manager: {
    email: 'manager@demo.com',
    password: 'Demo@1234',
    name: 'Vikram Kulkarni',
    roleTag: 'WARD MANAGER',
    avatar: 'VK'
  },
  administrator: {
    email: 'admin@demo.com',
    password: 'Demo@1234',
    name: 'Sneha Joshi',
    roleTag: 'ADMINISTRATOR',
    avatar: 'SJ'
  }
};

let currentRole = 'manager';
let authToken = '';
let currentOpenCaseId = null;
let searchDebounceTimeout = null;
let currentAiAnalysisData = null;

// =============================================================================
// INITIALIZATION
// =============================================================================
document.addEventListener('DOMContentLoaded', async () => {
  await loadCategoryDropdownOptions();
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

  // Adapt Nav tabs visibility based on Role
  updateRoleNavigationUI();

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
      updateNotificationsBadge();
    } else {
      console.error('Login failed for role:', roleKey);
    }
  } catch (err) {
    console.error('Error during role authentication:', err);
  }
}

function updateRoleNavigationUI() {
  const navEscalations = document.getElementById('nav-escalations');
  const navAudit = document.getElementById('nav-audit');
  const btnSweep = document.getElementById('btn-sla-sweep');
  const chatTypeSelect = document.getElementById('chat-type-select');

  if (currentRole === 'requester') {
    if (navEscalations) navEscalations.style.display = 'none';
    if (navAudit) navAudit.style.display = 'none';
    if (btnSweep) btnSweep.style.display = 'none';
    if (chatTypeSelect) chatTypeSelect.style.display = 'none';
    document.getElementById('nav-label-dashboard').innerText = 'My Dashboard';
    document.getElementById('nav-label-cases').innerText = 'My Complaints';
  } else if (currentRole === 'operator') {
    if (navEscalations) navEscalations.style.display = 'none';
    if (navAudit) navAudit.style.display = 'none';
    if (btnSweep) btnSweep.style.display = 'inline-flex';
    if (chatTypeSelect) chatTypeSelect.style.display = 'block';
    document.getElementById('nav-label-dashboard').innerText = 'Operator Queue';
    document.getElementById('nav-label-cases').innerText = 'Assigned Cases';
  } else if (currentRole === 'team_lead') {
    if (navEscalations) navEscalations.style.display = 'flex';
    if (navAudit) navAudit.style.display = 'none';
    if (btnSweep) btnSweep.style.display = 'inline-flex';
    if (chatTypeSelect) chatTypeSelect.style.display = 'block';
    document.getElementById('nav-label-dashboard').innerText = 'Squad Workload';
    document.getElementById('nav-label-cases').innerText = 'Team Cases';
  } else {
    // Manager & Administrator
    if (navEscalations) navEscalations.style.display = 'flex';
    if (navAudit) navAudit.style.display = 'flex';
    if (btnSweep) btnSweep.style.display = 'inline-flex';
    if (chatTypeSelect) chatTypeSelect.style.display = 'block';
    document.getElementById('nav-label-dashboard').innerText = 'Executive Analytics';
    document.getElementById('nav-label-cases').innerText = 'All Cases';
  }

  // Ensure an accessible tab is shown
  const activePane = document.querySelector('.tab-pane.active');
  if (activePane && (activePane.id === 'tab-audit' || activePane.id === 'tab-escalations')) {
    if (currentRole === 'requester' || (currentRole === 'operator' && activePane.id === 'tab-audit')) {
      showTab('dashboard');
    }
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
// 1. DASHBOARD & ROLE-BASED ANALYTICS
// =============================================================================
async function loadDashboardData() {
  try {
    if (currentRole === 'requester') {
      await loadCitizenDashboard();
    } else if (currentRole === 'operator') {
      await loadOperatorDashboard();
    } else if (currentRole === 'team_lead') {
      await loadTeamLeadDashboard();
    } else {
      await loadExecutiveDashboard();
    }
  } catch (err) {
    console.error('Error loading dashboard analytics:', err);
  }
}

// 1.A Citizen Dashboard
async function loadCitizenDashboard() {
  document.getElementById('dashboard-title').innerText = 'Citizen Grievance Portal';
  document.getElementById('dashboard-desc').innerText = 'Track the real-time lifecycle, field inspections, and AI resolution status of your complaints.';

  document.getElementById('kpi-label-1').innerText = 'TOTAL REPORTED';
  document.getElementById('kpi-label-2').innerText = 'ACTIVE / IN-PROGRESS';
  document.getElementById('kpi-label-3').innerText = 'WAITING CITIZEN INFO';
  document.getElementById('kpi-label-4').innerText = 'RESOLVED / CLOSED';

  document.getElementById('kpi-sub-1').innerText = 'Your registered grievances';
  document.getElementById('kpi-sub-2').innerText = 'Being handled by squad';
  document.getElementById('kpi-sub-3').innerText = 'Requires your reply';
  document.getElementById('kpi-sub-4').innerText = 'Verified solutions';

  const res = await fetch(`${API_BASE}/analytics/citizen`, { headers: getAuthHeaders() });
  if (!res.ok) return;
  const data = await res.json();

  document.getElementById('kpi-total').innerText = data.total_reported || 0;
  document.getElementById('kpi-active').innerText = data.active_count || 0;
  document.getElementById('kpi-sla').innerText = data.waiting_info_count || 0;
  document.getElementById('kpi-resolved').innerText = data.resolved_count || 0;

  // Render Citizen Recent Activity
  document.getElementById('ai-insights-header').innerText = '📑 Your Grievance Activity Log';
  document.getElementById('ai-insights-tag').innerText = 'TIMELINE';
  const insightsList = document.getElementById('ai-insights-list');
  insightsList.innerHTML = '';

  if (data.recent_activity && data.recent_activity.length > 0) {
    data.recent_activity.forEach(act => {
      insightsList.innerHTML += `
        <div class="ai-box" style="margin: 6px 0; border-left: 3px solid #3B82F6;">
          <div class="ai-box-header">
            <span><strong>${act.case_number}:</strong> ${act.title}</span>
            <span style="font-size: 11px; color: #94A3B8;">${new Date(act.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
          </div>
          <div style="font-size: 12px; color: #CBD5E1;">${act.action} — ${act.notes || 'Status updated'}</div>
        </div>
      `;
    });
  } else {
    insightsList.innerHTML = '<div style="color: #64748B; font-size: 13px; padding: 12px;">No activity yet. Click "+ Report Grievance" above to submit a new complaint.</div>';
  }

  // Right Panel for Citizen
  document.getElementById('panel-right-title').innerText = '🏛️ Municipal Citizen Services';
  const rightHead = document.getElementById('right-table-head');
  rightHead.innerHTML = '<tr><th>Service Feature</th><th>Details</th></tr>';
  const wardTbody = document.getElementById('ward-metrics-body');
  wardTbody.innerHTML = `
    <tr><td><strong>AI Auto-Triage</strong></td><td>Automated categorisation and priority routing within seconds.</td></tr>
    <tr><td><strong>SLA Guarantee</strong></td><td>Standard 24h - 48h emergency response time across all 5 wards.</td></tr>
    <tr><td><strong>Direct Chat</strong></td><td>Communicate directly with field squad operators and engineers.</td></tr>
    <tr><td><strong>Citizen Closure</strong></td><td>You have the final authority to confirm or reject field repairs.</td></tr>
  `;
}

// 1.B Field Operator Dashboard
async function loadOperatorDashboard() {
  document.getElementById('dashboard-title').innerText = 'Field Operations & Dispatch Queue';
  document.getElementById('dashboard-desc').innerText = 'Manage your daily assigned tickets, field inspections, and citizen inquiries.';

  document.getElementById('kpi-label-1').innerText = 'MY ACTIVE QUEUE';
  document.getElementById('kpi-label-2').innerText = 'HIGH PRIORITY';
  document.getElementById('kpi-label-3').innerText = 'WAITING CITIZEN INFO';
  document.getElementById('kpi-label-4').innerText = 'COMPLETED THIS WEEK';

  document.getElementById('kpi-sub-1').innerText = 'Currently assigned to you';
  document.getElementById('kpi-sub-2').innerText = 'Requires urgent inspection';
  document.getElementById('kpi-sub-3').innerText = 'Awaiting citizen reply';
  document.getElementById('kpi-sub-4').innerText = 'Successfully resolved';

  const res = await fetch(`${API_BASE}/analytics/operator`, { headers: getAuthHeaders() });
  if (!res.ok) return;
  const data = await res.json();

  document.getElementById('kpi-total').innerText = data.assigned_active_count || 0;
  document.getElementById('kpi-active').innerText = data.high_priority_count || 0;
  document.getElementById('kpi-sla').innerText = data.waiting_info_count || 0;
  document.getElementById('kpi-resolved').innerText = data.completed_this_week_count || 0;

  // Insights / Action items for Operator
  document.getElementById('ai-insights-header').innerText = '⚡ Operator Action Items & Tasks';
  document.getElementById('ai-insights-tag').innerText = 'QUEUE STATUS';
  const insightsList = document.getElementById('ai-insights-list');
  insightsList.innerHTML = `
    <div class="ai-box" style="margin: 6px 0;">
      <div class="ai-box-header">
        <span>📋 Pending Subtasks</span>
        <span class="badge badge-assigned">${data.pending_tasks_count || 0} PENDING</span>
      </div>
      <div style="font-size: 12px; color: #CBD5E1;">Actionable tasks requiring field execution or photographic proof.</div>
    </div>
    <div class="ai-box" style="margin: 6px 0;">
      <div class="ai-box-header">
        <span>⚠️ Escalation Risk</span>
        <span class="badge badge-${data.active_escalations_count > 0 ? 'high' : 'low'}">${data.active_escalations_count || 0} ACTIVE</span>
      </div>
      <div style="font-size: 12px; color: #CBD5E1;">Tickets at risk of SLA breach or requiring supervisor intervention.</div>
    </div>
  `;

  // Right table for Operator
  document.getElementById('panel-right-title').innerText = '📍 Field Quick Guidelines';
  const rightHead = document.getElementById('right-table-head');
  rightHead.innerHTML = '<tr><th>Workflow Step</th><th>Action Instruction</th></tr>';
  const wardTbody = document.getElementById('ward-metrics-body');
  wardTbody.innerHTML = `
    <tr><td><strong>1. Claim Ticket</strong></td><td>Claim reported tickets from Case Management to begin work.</td></tr>
    <tr><td><strong>2. Site Inspection</strong></td><td>Log field findings or request clarification from citizen.</td></tr>
    <tr><td><strong>3. Propose Resolution</strong></td><td>Submit completed repair notes; citizen gets notified instantly.</td></tr>
  `;
}

// 1.C Team Lead Dashboard
async function loadTeamLeadDashboard() {
  document.getElementById('dashboard-title').innerText = 'Squad Engineering Workload & Team Roster';
  document.getElementById('dashboard-desc').innerText = 'Supervise squad ticket distribution, monitor SLA compliance, and dispatch operators.';

  document.getElementById('kpi-label-1').innerText = 'SQUAD CASES';
  document.getElementById('kpi-label-2').innerText = 'ACTIVE IN FIELD';
  document.getElementById('kpi-label-3').innerText = 'SLA COMPLIANCE';
  document.getElementById('kpi-label-4').innerText = 'UNASSIGNED QUEUE';

  document.getElementById('kpi-sub-1').innerText = 'Total squad assigned';
  document.getElementById('kpi-sub-2').innerText = 'Ongoing field jobs';
  document.getElementById('kpi-sub-3').innerText = 'Target > 85%';
  document.getElementById('kpi-sub-4').innerText = 'Pending assignment';

  const res = await fetch(`${API_BASE}/analytics/team-lead`, { headers: getAuthHeaders() });
  if (!res.ok) return;
  const data = await res.json();

  document.getElementById('kpi-total').innerText = data.total_cases || 0;
  document.getElementById('kpi-active').innerText = data.active_cases || 0;
  document.getElementById('kpi-sla').innerText = `${data.sla_compliance_percent || 100}%`;
  document.getElementById('kpi-resolved').innerText = data.unassigned_cases || 0;

  // AI & Squad overview
  document.getElementById('ai-insights-header').innerText = '🤖 Squad AI Dispatch Insights';
  document.getElementById('ai-insights-tag').innerText = 'TEAM INTEL';
  const insightsList = document.getElementById('ai-insights-list');
  insightsList.innerHTML = `
    <div class="ai-box" style="margin: 6px 0;">
      <div class="ai-box-header">
        <span>Team: <strong>${data.team_name || 'Road Maintenance Squad Alpha'}</strong></span>
        <span class="badge badge-assigned">${data.active_escalations || 0} Escalations</span>
      </div>
      <div style="font-size: 12px; color: #CBD5E1;">At-risk SLA cases: <strong>${data.at_risk_cases || 0}</strong>. Average resolution time: <strong>${data.avg_resolution_time_hours || 4.2} hours</strong>.</div>
    </div>
  `;

  // Operator workload table
  document.getElementById('panel-right-title').innerText = '👷 Operator Workload & Productivity';
  const rightHead = document.getElementById('right-table-head');
  rightHead.innerHTML = '<tr><th>Operator</th><th>Active</th><th>Completed</th><th>Overdue</th></tr>';
  const wardTbody = document.getElementById('ward-metrics-body');
  wardTbody.innerHTML = '';

  if (data.operator_workloads && data.operator_workloads.length > 0) {
    data.operator_workloads.forEach(op => {
      wardTbody.innerHTML += `
        <tr>
          <td><strong>${op.operator_name}</strong></td>
          <td><span class="badge badge-assigned">${op.active_cases}</span></td>
          <td>${op.completed_cases}</td>
          <td><span class="badge badge-${op.overdue_cases > 0 ? 'high' : 'low'}">${op.overdue_cases}</span></td>
        </tr>
      `;
    });
  } else {
    wardTbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#64748B;">All squad operators are available.</td></tr>';
  }
}

// 1.D Executive Dashboard (Manager & Admin)
async function loadExecutiveDashboard() {
  document.getElementById('dashboard-title').innerText = 'Executive Ward Overview';
  document.getElementById('dashboard-desc').innerText = 'Real-time civic intelligence, SLA compliance, and AI operational anomaly alerts.';

  document.getElementById('kpi-label-1').innerText = 'TOTAL COMPLAINTS';
  document.getElementById('kpi-label-2').innerText = 'ACTIVE / IN-PROGRESS';
  document.getElementById('kpi-label-3').innerText = 'SLA COMPLIANCE';
  document.getElementById('kpi-label-4').innerText = 'RESOLVED / CONFIRMED';

  document.getElementById('kpi-sub-1').innerText = 'Across all 5 wards';
  document.getElementById('kpi-sub-2').innerText = 'Field investigation & repair';
  document.getElementById('kpi-sub-3').innerText = 'Target: >85%';
  document.getElementById('kpi-sub-4').innerText = 'Citizen verified closure';

  const res = await fetch(`${API_BASE}/analytics/manager`, { headers: getAuthHeaders() });
  if (!res.ok) return;
  const data = await res.json();

  document.getElementById('kpi-total').innerText = data.total_cases || 0;
  document.getElementById('kpi-active').innerText = data.active_cases || 0;
  document.getElementById('kpi-sla').innerText = `${data.sla_compliance_percent || 100}%`;
  document.getElementById('kpi-resolved').innerText = data.resolved_cases || 0;

  // Render AI Operational Insights
  document.getElementById('ai-insights-header').innerText = '🤖 AI Operational Intelligence & Hotspots';
  document.getElementById('ai-insights-tag').innerText = 'LIVE AI SCAN';
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
    insightsList.innerHTML = '<div style="color: #64748B; font-size: 13px; padding: 12px;">All municipal operations running within healthy SLA boundaries.</div>';
  }

  // Render Ward Performance Table
  document.getElementById('panel-right-title').innerText = '📍 Ward Performance & Risk Heatmap';
  const rightHead = document.getElementById('right-table-head');
  rightHead.innerHTML = '<tr><th>Ward</th><th>Total</th><th>Active</th><th>Top Issue</th><th>Risk</th></tr>';
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
            <div>${c.ward || 'Ward 12 - North'}</div>
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
// 3. CASE DETAIL, AI COPILOT & UNIFIED TIMELINE
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
      document.getElementById('detail-location-text').innerText = `${c.ward} | ${c.landmark || 'No landmark specified'}`;
      document.getElementById('detail-category-text').innerText = c.category ? `${c.category.name}` : 'General Municipal Works';

      const statusPill = document.getElementById('detail-status-pill');
      statusPill.className = `badge badge-${c.status}`;
      statusPill.innerText = c.status.replace('_', ' ').toUpperCase();

      const priorityPill = document.getElementById('detail-priority-pill');
      priorityPill.className = `badge badge-${c.priority}`;
      priorityPill.innerText = c.priority.toUpperCase();

      renderRoleActions(c);
    }

    // 2. Fetch AI Analysis
    const aiRes = await fetch(`${API_BASE}/cases/${caseId}/ai-analysis`, { headers: getAuthHeaders() });
    if (aiRes.ok) {
      const ai = await aiRes.json();
      currentAiAnalysisData = ai;
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
      stream.innerHTML = '<div style="color: #64748B; font-size: 12px; padding: 12px;">No activity recorded yet.</div>';
      return;
    }

    data.timeline.forEach(item => {
      const timeStr = new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const isInternal = item.is_internal;
      stream.innerHTML += `
        <div class="timeline-card" style="${isInternal ? 'border-left: 3px solid #8B5CF6; background: rgba(139, 92, 246, 0.05);' : ''}">
          <div class="timeline-card-header">
            <span class="timeline-actor">
              ${item.actor_name || 'System / AI'} 
              <span style="font-size: 10px; color: ${isInternal ? '#A78BFA' : '#38BDF8'};">
                (${isInternal ? '🔒 INTERNAL NOTE' : item.actor_role || item.event_type})
              </span>
            </span>
            <span class="timeline-time">${timeStr}</span>
          </div>
          <div class="timeline-text"><strong>${item.title}:</strong> ${item.description || ''}</div>
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
    } else {
      panel.innerHTML = `
        <div style="font-size: 12px; color: #94A3B8; background: rgba(255,255,255,0.03); padding: 10px; border-radius: 8px;">
          ℹ️ Your complaint is currently in <strong>${caseObj.status.replace('_', ' ').toUpperCase()}</strong> status. You will receive an alert once field operations propose a resolution.
        </div>
      `;
    }
  } else if (currentRole === 'operator') {
    if (caseObj.status === 'reported') {
      panel.innerHTML = `
        <button class="btn btn-primary btn-sm" onclick="claimCase(${caseObj.id})" style="width: 100%;">
          👷 Take Ownership & Claim Case
        </button>
      `;
    } else if (caseObj.status === 'assigned' || caseObj.status === 'investigated' || caseObj.status === 'action_taken') {
      panel.innerHTML = `
        <button class="btn btn-primary btn-sm" onclick="proposeResolution(${caseObj.id})" style="width: 100%; margin-bottom: 6px;">
          ✨ Propose Field Resolution
        </button>
        <button class="btn btn-outline btn-sm" onclick="logFieldInvestigation(${caseObj.id})" style="width: 100%; margin-bottom: 6px;">
          🔍 Log Field Investigation
        </button>
        <button class="btn btn-outline btn-sm" onclick="requestClarification(${caseObj.id})" style="width: 100%;">
          ❓ Request Info from Citizen
        </button>
      `;
    }
  } else if (currentRole === 'team_lead' || currentRole === 'manager' || currentRole === 'administrator') {
    panel.innerHTML = `
      <button class="btn btn-secondary btn-sm" onclick="manualEscalateCase(${caseObj.id})" style="width: 100%; margin-bottom: 6px;">
        ⚠️ Trigger SLA Escalation
      </button>
      <button class="btn btn-outline btn-sm" onclick="reassignCasePrompt(${caseObj.id})" style="width: 100%;">
        👥 Assign / Transfer Squad
      </button>
    `;
  }
}

// Case Action Handlers
async function confirmResolution(caseId) {
  const notes = prompt('Enter citizen verification feedback:', 'Inspected and verified on site. Road repaired cleanly.');
  if (notes === null) return;

  const res = await fetch(`${API_BASE}/cases/${caseId}/confirm-resolution`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ notes })
  });
  if (res.ok) {
    alert('Resolution confirmed! Complaint closed.');
    openCaseDetail(caseId);
    loadCases();
    loadDashboardData();
  } else {
    const err = await res.json();
    alert(`Error: ${err.detail || 'Could not confirm resolution'}`);
  }
}

async function rejectResolution(caseId) {
  const reason = prompt('Enter reason for rejecting resolution:', 'Issue still persists and requires additional asphalt compaction.');
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
    loadDashboardData();
  } else {
    const err = await res.json();
    alert(`Error: ${err.detail || 'Could not reject resolution'}`);
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
  const notes = prompt('Enter field repair notes:', 'Pothole filled with hot-mix asphalt and compacted level with road surface.');
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
  } else {
    const err = await res.json();
    alert(`Error: ${err.detail || 'Could not propose resolution'}`);
  }
}

async function logFieldInvestigation(caseId) {
  const findings = prompt('Enter site inspection findings:', 'Subsurface water erosion detected around stormwater pipe.');
  if (!findings) return;

  const res = await fetch(`${API_BASE}/cases/${caseId}/investigations`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      observations: 'On-site engineering assessment completed.',
      findings: findings,
      actions_taken: 'Site barricaded with safety cones; gravel layer reinforced.'
    })
  });
  if (res.ok) {
    alert('Field investigation logged in unified timeline!');
    loadCaseTimeline(caseId);
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
    updateNotificationsBadge();
  }
}

async function reassignCasePrompt(caseId) {
  const squad = prompt('Enter squad ID or department ID to transfer:', '1');
  if (!squad) return;

  const res = await fetch(`${API_BASE}/cases/${caseId}/assignment`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ department_id: parseInt(squad), reason: 'Supervisor transfer' })
  });
  if (res.ok) {
    alert('Case reassigned!');
    openCaseDetail(caseId);
    loadCases();
  }
}

// AI Copilot Actions
async function runAiTriageForCurrentCase() {
  if (!currentOpenCaseId) return;
  const res = await fetch(`${API_BASE}/cases/${currentOpenCaseId}/ai-analysis`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (res.ok) {
    alert('AI Triage re-calculated with latest telemetry!');
    openCaseDetail(currentOpenCaseId);
  }
}

async function applyAiSuggestionsForCurrentCase() {
  if (!currentOpenCaseId || !currentAiAnalysisData) return;

  const res = await fetch(`${API_BASE}/cases/${currentOpenCaseId}/ai/apply-suggestions`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      apply_category: true,
      apply_priority: true,
      apply_team: true
    })
  });

  if (res.ok) {
    alert('AI Suggested Category & Priority applied to live case!');
    openCaseDetail(currentOpenCaseId);
    loadCases();
  } else {
    const err = await res.json();
    alert(`Error: ${err.detail || 'Failed to apply AI suggestions'}`);
  }
}

async function viewCaseSummaryForCurrentCase() {
  if (!currentOpenCaseId) return;
  const res = await fetch(`${API_BASE}/cases/${currentOpenCaseId}/summary`, { headers: getAuthHeaders() });
  if (res.ok) {
    const summary = await res.json();
    const blockers = (summary.unresolved_blockers && summary.unresolved_blockers.length > 0) 
      ? summary.unresolved_blockers.join('\n- ') 
      : 'None (Workflow on track)';
    alert(`📄 AI Comprehensive Case Journey Summary:\n\nCase: ${summary.case_number} (${summary.current_stage})\n\n${summary.summary}\n\nUnresolved Blockers / Items:\n- ${blockers}\n\nLast Activity: ${summary.last_activity || 'N/A'}`);
  }
}

async function triggerAiDraftCommunication() {
  if (!currentOpenCaseId) return;
  const res = await fetch(`${API_BASE}/cases/${currentOpenCaseId}/ai/draft-communication`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      draft_type: 'progress_update',
      context_notes: 'Site inspection completed and materials dispatched.'
    })
  });

  if (res.ok) {
    const draft = await res.json();
    document.getElementById('chat-input').value = draft.body_text || draft.subject;
  }
}

async function handleSendMessage(e) {
  e.preventDefault();
  const input = document.getElementById('chat-input');
  const message = input.value.trim();
  if (!message || !currentOpenCaseId) return;

  const typeSelect = document.getElementById('chat-type-select');
  const isInternalNote = typeSelect && typeSelect.value === 'internal_note' && currentRole !== 'requester';

  let res;
  if (isInternalNote) {
    res = await fetch(`${API_BASE}/cases/${currentOpenCaseId}/internal-notes`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ note: message, note_type: 'general' })
    });
  } else {
    res = await fetch(`${API_BASE}/cases/${currentOpenCaseId}/messages`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ message, message_type: 'general' })
    });
  }

  if (res.ok) {
    input.value = '';
    loadCaseTimeline(currentOpenCaseId);
  }
}

// =============================================================================
// 4. REPORT NEW GRIEVANCE
// =============================================================================
async function loadCategoryDropdownOptions() {
  try {
    const res = await fetch(`${API_BASE}/organization/categories`);
    if (!res.ok) return;
    const cats = await res.json();
    const select = document.getElementById('case-in-category');
    if (!select) return;

    cats.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.innerText = `${c.name} (${c.sla_hours}h SLA)`;
      select.appendChild(opt);
    });
  } catch (err) {
    console.warn('Could not preload categories:', err);
  }
}

async function handleCreateCase(e) {
  e.preventDefault();
  const title = document.getElementById('case-in-title').value;
  const description = document.getElementById('case-in-description').value;
  const categoryIdVal = document.getElementById('case-in-category').value;
  const ward = document.getElementById('case-in-ward').value;
  const landmark = document.getElementById('case-in-landmark').value;
  const priority = document.getElementById('case-in-priority').value;
  const severity = document.getElementById('case-in-severity').value;

  const payload = {
    title,
    description,
    ward,
    landmark,
    priority,
    severity
  };

  if (categoryIdVal) {
    payload.category_id = parseInt(categoryIdVal);
  }

  try {
    const res = await fetch(`${API_BASE}/cases`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const created = await res.json();
      closeModal('modal-new-case');
      document.getElementById('new-case-form').reset();
      alert(`Complaint registered successfully! Case Number: ${created.case_number}`);
      loadCases();
      loadDashboardData();
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
    loadDashboardData();
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
          <td><strong>${l.actor_name || 'System'}</strong> <span style="font-size: 10px; color: #64748B;">(${l.actor_role || 'system'})</span></td>
          <td><strong>${l.action}</strong></td>
          <td><span class="badge">${l.case_number || 'Case #' + l.case_id}</span></td>
          <td style="font-size: 12px;">${l.notes || l.old_value + ' ➔ ' + l.new_value || ''}</td>
          <td>${l.actor_role === 'ai_engine' ? '<span class="badge badge-ai">AI ENGINE</span>' : '<span style="color: #64748B;">Human</span>'}</td>
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
    const data = await res.json();
    const items = data.items || [];

    const list = document.getElementById('notifications-list');
    list.innerHTML = '';

    const unreadCount = data.unread_count !== undefined ? data.unread_count : items.filter(n => !n.is_read).length;
    document.getElementById('notifications-count').innerText = unreadCount;

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

async function updateNotificationsBadge() {
  try {
    const res = await fetch(`${API_BASE}/notifications/unread-count`, { headers: getAuthHeaders() });
    if (res.ok) {
      const data = await res.json();
      document.getElementById('notifications-count').innerText = data.unread_count || 0;
    }
  } catch (e) {}
}

async function markAllNotificationsRead() {
  await fetch(`${API_BASE}/notifications/mark-all-read`, {
    method: 'POST',
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
