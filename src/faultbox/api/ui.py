"""Embedded single-page Web UI dashboard for FaultBox."""

from __future__ import annotations


def get_ui_html() -> str:
    """Return standalone HTML5 application for the browser dashboard."""
    return """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FaultBox Control Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0a0e14;
      --bg-raised: #111820;
      --card-bg: #151d28;
      --card-bg-hover: #1a2332;
      --border: #1e2a3a;
      --border-focus: #3b82f6;
      --text: #cbd5e1;
      --text-muted: #64748b;
      --text-bright: #f1f5f9;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --green: #22c55e;
      --green-dim: rgba(34, 197, 94, 0.12);
      --red: #ef4444;
      --red-dim: rgba(239, 68, 68, 0.10);
      --yellow: #eab308;
      --yellow-dim: rgba(234, 179, 8, 0.10);
      --orange: #f97316;
      --orange-dim: rgba(249, 115, 22, 0.10);
      --purple: #a855f7;
      --purple-dim: rgba(168, 85, 247, 0.10);
      --cyan: #06b6d4;
      --cyan-dim: rgba(6, 182, 212, 0.10);
      --radius: 10px;
      --radius-sm: 6px;
      --shadow: 0 1px 3px rgba(0,0,0,0.3), 0 4px 12px rgba(0,0,0,0.2);
      --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    html { scroll-behavior: smooth; }

    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: var(--font);
      font-size: 14px;
      line-height: 1.6;
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    .app-shell {
      max-width: 1320px;
      margin: 0 auto;
      padding: 20px 24px 40px;
    }

    /* ── Header ── */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      padding-bottom: 20px;
      margin-bottom: 24px;
      border-bottom: 1px solid var(--border);
    }
    .header-brand {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .header-logo {
      width: 38px;
      height: 38px;
      flex-shrink: 0;
    }
    .header-text h1 {
      font-size: 20px;
      font-weight: 700;
      color: var(--text-bright);
      letter-spacing: -0.3px;
      line-height: 1.2;
    }
    .header-text .subtitle {
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 400;
      margin-top: 2px;
    }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }

    /* ── Badges ── */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.3px;
      text-transform: uppercase;
      white-space: nowrap;
      transition: all 0.2s ease;
    }
    .badge-green { background: var(--green-dim); color: var(--green); border: 1px solid rgba(34,197,94,0.25); }
    .badge-red { background: var(--red-dim); color: var(--red); border: 1px solid rgba(239,68,68,0.25); }
    .badge-yellow { background: var(--yellow-dim); color: var(--yellow); border: 1px solid rgba(234,179,8,0.25); }
    .badge::before {
      content: '';
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: currentColor;
      flex-shrink: 0;
    }

    /* ── KPI Cards ── */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 14px;
      margin-bottom: 24px;
    }
    .kpi-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 18px 20px;
      position: relative;
      overflow: hidden;
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
      border-color: rgba(59, 130, 246, 0.3);
      box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.1);
    }
    .kpi-card canvas {
      position: absolute;
      bottom: 0;
      left: 0;
      width: 100%;
      height: 36px;
      opacity: 0.25;
    }
    .kpi-title {
      font-size: 11px;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.5px;
    }
    .kpi-value {
      font-size: 26px;
      font-weight: 700;
      color: var(--text-bright);
      margin-top: 6px;
      font-variant-numeric: tabular-nums;
    }

    /* ── Panel ── */
    .panel {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      margin-bottom: 24px;
      box-shadow: var(--shadow);
    }
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      padding: 16px 20px;
      border-bottom: 1px solid var(--border);
      background: var(--bg-raised);
    }
    .panel-title {
      font-weight: 600;
      font-size: 15px;
      color: var(--text-bright);
    }

    /* ── Table ── */
    .table-wrapper { overflow-x: auto; -webkit-overflow-scrolling: touch; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
    th {
      background: rgba(255,255,255,0.02);
      color: var(--text-muted);
      padding: 10px 16px;
      border-bottom: 1px solid var(--border);
      font-weight: 600;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      white-space: nowrap;
    }
    td {
      padding: 14px 16px;
      border-bottom: 1px solid var(--border);
      vertical-align: middle;
    }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: rgba(255,255,255,0.015); }
    td code {
      font-family: var(--mono);
      font-size: 12px;
      background: rgba(255,255,255,0.05);
      padding: 2px 7px;
      border-radius: 4px;
      color: var(--text-bright);
    }

    /* ── Buttons ── */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      background: var(--bg-raised);
      color: var(--text);
      border: 1px solid var(--border);
      padding: 7px 14px;
      border-radius: var(--radius-sm);
      cursor: pointer;
      font-size: 12px;
      font-weight: 500;
      font-family: var(--font);
      white-space: nowrap;
      transition: all 0.15s ease;
      min-height: 34px;
    }
    .btn:hover { background: #1e2a3a; border-color: #2a3a4e; }
    .btn:active { transform: scale(0.97); }
    .btn-primary {
      background: var(--accent);
      color: #fff;
      border-color: transparent;
      font-weight: 600;
    }
    .btn-primary:hover { background: var(--accent-hover); }
    .btn-danger {
      background: var(--red-dim);
      color: var(--red);
      border-color: rgba(239,68,68,0.2);
    }
    .btn-danger:hover { background: rgba(239,68,68,0.2); border-color: rgba(239,68,68,0.4); }
    .btn-icon {
      padding: 7px 9px;
      min-width: 34px;
      min-height: 34px;
    }
    .btn-sm { padding: 4px 10px; font-size: 11px; min-height: 28px; }

    /* ── Toxic Tags ── */
    .toxic-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 10px;
      border-radius: 16px;
      font-size: 11px;
      font-weight: 500;
      margin: 2px 3px;
      white-space: nowrap;
      transition: all 0.15s ease;
    }
    /* Latency / Delay category */
    .toxic-latency { background: var(--yellow-dim); border: 1px solid rgba(234,179,8,0.25); color: var(--yellow); }
    .toxic-waveform_latency { background: var(--yellow-dim); border: 1px solid rgba(234,179,8,0.25); color: var(--yellow); }
    /* Throughput / Throttle category */
    .toxic-bandwidth { background: var(--cyan-dim); border: 1px solid rgba(6,182,212,0.25); color: var(--cyan); }
    .toxic-timeout { background: var(--orange-dim); border: 1px solid rgba(249,115,22,0.25); color: var(--orange); }
    /* Destructive / Error category */
    .toxic-reset_peer { background: var(--red-dim); border: 1px solid rgba(239,68,68,0.25); color: var(--red); }
    .toxic-http_error { background: var(--red-dim); border: 1px solid rgba(239,68,68,0.25); color: var(--red); }
    .toxic-grpc_fault { background: var(--red-dim); border: 1px solid rgba(239,68,68,0.25); color: var(--red); }
    /* Corruption / Manipulation category */
    .toxic-corrupt { background: var(--purple-dim); border: 1px solid rgba(168,85,247,0.25); color: var(--purple); }
    .toxic-slicer { background: var(--purple-dim); border: 1px solid rgba(168,85,247,0.25); color: var(--purple); }
    .toxic-tls_fault { background: var(--purple-dim); border: 1px solid rgba(168,85,247,0.25); color: var(--purple); }
    /* Behavioral category */
    .toxic-flapping { background: var(--orange-dim); border: 1px solid rgba(249,115,22,0.25); color: var(--orange); }

    .toxic-delete {
      cursor: pointer;
      font-weight: bold;
      font-size: 14px;
      line-height: 1;
      opacity: 0.7;
      padding: 2px;
      min-width: 18px;
      min-height: 18px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    .toxic-delete:hover { opacity: 1; }

    .pristine-tag {
      color: var(--green);
      font-size: 12px;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .pristine-tag::before {
      content: '';
      width: 6px;
      height: 6px;
      background: var(--green);
      border-radius: 50%;
    }

    .proxy-actions {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }

    /* ── Modal ── */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(4px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 100;
      padding: 20px;
      animation: fadeIn 0.15s ease;
    }
    .modal-overlay.active { display: flex; }
    .modal {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      width: 100%;
      max-width: 520px;
      max-height: 90vh;
      overflow-y: auto;
      padding: 24px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
      animation: slideUp 0.2s ease;
    }
    .modal-title {
      font-size: 17px;
      font-weight: 700;
      color: var(--text-bright);
      margin-bottom: 20px;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--border);
    }
    .form-group { margin-bottom: 16px; }
    .form-group label {
      display: block;
      font-size: 12px;
      color: var(--text-muted);
      font-weight: 600;
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }
    input, select, textarea {
      width: 100%;
      background: var(--bg);
      border: 1px solid var(--border);
      color: var(--text-bright);
      padding: 9px 12px;
      border-radius: var(--radius-sm);
      font-size: 13px;
      font-family: var(--font);
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    input:focus, select:focus, textarea:focus {
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
    }
    textarea { font-family: var(--mono); font-size: 12px; line-height: 1.5; resize: vertical; }
    select { cursor: pointer; }
    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .form-hint {
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 4px;
    }
    .modal-actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid var(--border);
    }

    /* ── Confirm Dialog ── */
    .confirm-dialog .modal { max-width: 400px; text-align: center; }
    .confirm-message { font-size: 14px; color: var(--text); margin-bottom: 4px; line-height: 1.5; }
    .confirm-sub { font-size: 12px; color: var(--text-muted); }

    /* ── Toast Notifications ── */
    .toast-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 200;
      display: flex;
      flex-direction: column;
      gap: 10px;
      pointer-events: none;
    }
    .toast {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 12px 18px;
      font-size: 13px;
      color: var(--text);
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
      pointer-events: auto;
      animation: slideInRight 0.3s ease, fadeOut 0.3s ease 3.5s forwards;
      max-width: 380px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .toast-success { border-left: 3px solid var(--green); }
    .toast-error { border-left: 3px solid var(--red); }
    .toast-icon { font-size: 16px; flex-shrink: 0; }

    /* ── Empty State ── */
    .empty-state {
      text-align: center;
      padding: 48px 20px;
      color: var(--text-muted);
    }
    .empty-state svg { margin-bottom: 12px; opacity: 0.3; }
    .empty-state p { font-size: 13px; margin-top: 8px; }

    /* ── Animations ── */
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes slideInRight { from { opacity: 0; transform: translateX(40px); } to { opacity: 1; transform: translateX(0); } }
    @keyframes fadeOut { from { opacity: 1; } to { opacity: 0; } }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

    /* ── Responsive ── */
    @media (max-width: 768px) {
      .app-shell { padding: 16px; }
      header { gap: 12px; }
      .header-text h1 { font-size: 17px; }
      .kpi-grid { grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
      .kpi-card { padding: 14px; }
      .kpi-value { font-size: 22px; }
      .panel-header { padding: 12px 16px; }
      th, td { padding: 10px 12px; }
      .form-row { grid-template-columns: 1fr; }
      .modal { padding: 18px; }
      .proxy-actions { gap: 4px; }
      .btn { padding: 6px 10px; font-size: 11px; }
    }
    @media (max-width: 480px) {
      .header-brand { gap: 10px; }
      .header-logo { width: 30px; height: 30px; }
      .header-text h1 { font-size: 15px; }
      .header-text .subtitle { display: none; }
      .kpi-grid { grid-template-columns: 1fr 1fr; }
      .toast-container { left: 16px; right: 16px; bottom: 16px; }
      .toast { max-width: none; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <header>
      <div class="header-brand">
        <svg class="header-logo" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect width="40" height="40" rx="10" fill="#DBFF00"/>
          <path d="M12 8C10.5 9.5 9 12 9 15c0 2 .8 3.5 2 4.5.5.4 1 .7 1.5.9-.3.5-.5 1.2-.5 2 0 1.5.7 2.8 1.8 3.5C13.3 26.5 13 27.2 13 28c0 1.7 1.3 3 3 3h1c2.2 0 4-1.8 4-4v-1.5" stroke="#0a0e14" stroke-width="2" stroke-linecap="round"/>
          <path d="M22 10l-3 8h5l-4 10" stroke="#0a0e14" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="14" cy="13" r="1.2" fill="#0a0e14"/>
        </svg>
        <div class="header-text">
          <h1>FaultBox</h1>
          <div class="subtitle">Chaos Injection Proxy</div>
        </div>
      </div>
      <div class="header-actions">
        <span id="conn-status" class="badge badge-green">Live Feed</span>
        <button class="btn btn-primary" onclick="openModal('modal-proxy')">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M7 1v12M1 7h12"/></svg>
          New Proxy
        </button>
      </div>
    </header>

    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-title">Active Proxies</div>
        <div class="kpi-value" id="kpi-proxies">0</div>
        <canvas id="spark-proxies"></canvas>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Connections</div>
        <div class="kpi-value" id="kpi-conn-active">0</div>
        <canvas id="spark-conn"></canvas>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Throughput In</div>
        <div class="kpi-value" id="kpi-throughput-in">0 B/s</div>
        <canvas id="spark-in"></canvas>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Throughput Out</div>
        <div class="kpi-value" id="kpi-throughput-out">0 B/s</div>
        <canvas id="spark-out"></canvas>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Total Errors</div>
        <div class="kpi-value" id="kpi-errors">0</div>
        <canvas id="spark-errors"></canvas>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">Active Chaos Proxies</span>
        <button class="btn btn-sm" onclick="fetchProxies()">
          <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 6a5 5 0 019.47-2M11 6a5 5 0 01-9.47 2"/><path d="M1 1v3h3M11 11V8H8"/></svg>
          Refresh
        </button>
      </div>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Listen</th>
              <th>Upstream</th>
              <th>State</th>
              <th>Active Toxics</th>
              <th>Transferred</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="proxy-table-body">
            <tr>
              <td colspan="7">
                <div class="empty-state">
                  <svg width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path d="M12 6v6l4 2M22 12a10 10 0 11-20 0 10 10 0 0120 0z" stroke-linecap="round"/></svg>
                  <p>Loading proxies&hellip;</p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Create Proxy Modal -->
  <div class="modal-overlay" id="modal-proxy">
    <div class="modal">
      <div class="modal-title">Create New Proxy Route</div>
      <div class="form-group">
        <label>Proxy Name</label>
        <input type="text" id="new-proxy-name" placeholder="order-db">
        <div class="form-hint">Unique identifier for this proxy route</div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Listen Address</label>
          <input type="text" id="new-proxy-listen" placeholder="0.0.0.0:9000">
        </div>
        <div class="form-group">
          <label>Upstream Target</label>
          <input type="text" id="new-proxy-upstream" placeholder="127.0.0.1:5432">
        </div>
      </div>
      <div class="modal-actions">
        <button class="btn" onclick="closeModal('modal-proxy')">Cancel</button>
        <button class="btn btn-primary" onclick="submitCreateProxy()">Create Proxy</button>
      </div>
    </div>
  </div>

  <!-- Add Toxic Modal -->
  <div class="modal-overlay" id="modal-toxic">
    <div class="modal">
      <div class="modal-title">Attach Toxic to <span id="toxic-target-proxy" style="color: var(--accent);"></span></div>
      <input type="hidden" id="toxic-proxy-name">
      <div class="form-group">
        <label>Toxic Name</label>
        <input type="text" id="toxic-name" placeholder="latency-spike">
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Toxic Type</label>
          <select id="toxic-type" onchange="updateToxicFields()">
            <optgroup label="Latency &amp; Delay">
              <option value="latency">Latency</option>
              <option value="waveform_latency">Waveform Latency</option>
            </optgroup>
            <optgroup label="Throughput &amp; Throttling">
              <option value="bandwidth">Bandwidth Throttle</option>
              <option value="timeout">Timeout / Hang</option>
            </optgroup>
            <optgroup label="Connection Disruption">
              <option value="reset_peer">Reset Peer (TCP RST)</option>
              <option value="flapping">Flapping Connection</option>
            </optgroup>
            <optgroup label="Data Corruption">
              <option value="corrupt">Byte Corruption</option>
              <option value="slicer">Packet Slicer</option>
            </optgroup>
            <optgroup label="Protocol Errors">
              <option value="http_error">HTTP Error Status</option>
              <option value="grpc_fault">gRPC Fault</option>
              <option value="tls_fault">TLS / SSL Fault</option>
            </optgroup>
          </select>
        </div>
        <div class="form-group">
          <label>Direction</label>
          <select id="toxic-direction">
            <option value="both">Both Directions</option>
            <option value="inbound">Inbound (Client → Upstream)</option>
            <option value="outbound">Outbound (Upstream → Client)</option>
          </select>
        </div>
      </div>
      <div class="form-group">
        <label>Toxicity Probability</label>
        <div style="display: flex; align-items: center; gap: 12px;">
          <input type="range" id="toxic-probability" min="0" max="1" step="0.05" value="1.0"
                 oninput="document.getElementById('toxic-prob-display').textContent = (this.value * 100).toFixed(0) + '%'"
                 style="flex: 1; cursor: pointer;">
          <span id="toxic-prob-display" style="font-family: var(--mono); font-size: 13px; color: var(--text-bright); min-width: 40px; text-align: right;">100%</span>
        </div>
      </div>
      <div id="toxic-dynamic-fields"></div>
      <div class="form-group" id="toxic-advanced-json" style="display: none;">
        <label>Raw Attributes (JSON)</label>
        <textarea id="toxic-attributes" rows="4">{}</textarea>
        <div class="form-hint">Advanced: manually edit raw JSON attributes</div>
      </div>
      <div style="display: flex; justify-content: flex-end; margin-bottom: 4px;">
        <button class="btn btn-sm" onclick="toggleAdvancedJson()" style="font-size: 11px; color: var(--text-muted);">
          Toggle Raw JSON
        </button>
      </div>
      <div class="modal-actions">
        <button class="btn" onclick="closeModal('modal-toxic')">Cancel</button>
        <button class="btn btn-primary" onclick="submitAddToxic()">Attach Toxic</button>
      </div>
    </div>
  </div>

  <!-- Confirm Dialog -->
  <div class="modal-overlay confirm-dialog" id="modal-confirm">
    <div class="modal">
      <div class="modal-title" id="confirm-title">Confirm Action</div>
      <p class="confirm-message" id="confirm-message"></p>
      <p class="confirm-sub" id="confirm-sub"></p>
      <div class="modal-actions">
        <button class="btn" onclick="closeModal('modal-confirm')">Cancel</button>
        <button class="btn btn-danger" id="confirm-action-btn">Confirm</button>
      </div>
    </div>
  </div>

  <!-- Toast Container -->
  <div class="toast-container" id="toast-container"></div>

  <script>
    /* ── Toxic field definitions ── */
    const toxicFieldDefs = {
      latency: [
        { key: 'latency_ms', label: 'Latency (ms)', type: 'number', value: 250, min: 0, max: 60000 },
        { key: 'jitter_ms', label: 'Jitter (ms)', type: 'number', value: 50, min: 0, max: 10000 },
        { key: 'distribution', label: 'Distribution', type: 'select', value: 'uniform', options: ['uniform', 'normal', 'log_normal'] }
      ],
      waveform_latency: [
        { key: 'base_latency_ms', label: 'Base Latency (ms)', type: 'number', value: 100, min: 0 },
        { key: 'amplitude_ms', label: 'Amplitude (ms)', type: 'number', value: 300, min: 0 },
        { key: 'period_sec', label: 'Period (sec)', type: 'number', value: 15.0, min: 0.1, step: 0.1 },
        { key: 'waveform', label: 'Waveform', type: 'select', value: 'sine', options: ['sine', 'sawtooth', 'burst', 'brownian'] }
      ],
      bandwidth: [
        { key: 'rate_kbps', label: 'Rate (KB/s)', type: 'number', value: 50, min: 1 }
      ],
      reset_peer: [
        { key: 'byte_offset', label: 'Byte Offset', type: 'number', value: 1024, min: 0 },
        { key: 'timeout_ms', label: 'Timeout (ms)', type: 'number', value: 0, min: 0 }
      ],
      timeout: [
        { key: 'timeout_ms', label: 'Timeout Duration (ms)', type: 'number', value: 2000, min: 0 }
      ],
      corrupt: [
        { key: 'rate', label: 'Corruption Rate (0-1)', type: 'number', value: 0.05, min: 0, max: 1, step: 0.01 },
        { key: 'mode', label: 'Mode', type: 'select', value: 'bitflip', options: ['bitflip', 'random_byte'] }
      ],
      slicer: [
        { key: 'slice_size', label: 'Slice Size (bytes)', type: 'number', value: 64, min: 1 },
        { key: 'delay_ms', label: 'Inter-slice Delay (ms)', type: 'number', value: 10, min: 0 }
      ],
      flapping: [
        { key: 'up_duration_sec', label: 'Up Duration (sec)', type: 'number', value: 8.0, min: 0.1, step: 0.1 },
        { key: 'down_duration_sec', label: 'Down Duration (sec)', type: 'number', value: 4.0, min: 0.1, step: 0.1 },
        { key: 'down_action', label: 'Down Action', type: 'select', value: 'reset', options: ['reset', 'timeout', 'reject'] }
      ],
      http_error: [
        { key: 'status_code', label: 'HTTP Status Code', type: 'select', value: '503', options: ['400', '401', '403', '404', '429', '500', '502', '503', '504'] },
        { key: 'status_message', label: 'Status Message', type: 'text', value: 'Service Unavailable' },
        { key: 'body', label: 'Response Body', type: 'text', value: '{"error":"Service Unavailable"}' }
      ],
      grpc_fault: [
        { key: 'grpc_status', label: 'gRPC Status Code', type: 'select', value: '14', options: [
          { v: '0', l: '0 - OK' }, { v: '1', l: '1 - CANCELLED' }, { v: '2', l: '2 - UNKNOWN' },
          { v: '3', l: '3 - INVALID_ARGUMENT' }, { v: '4', l: '4 - DEADLINE_EXCEEDED' },
          { v: '5', l: '5 - NOT_FOUND' }, { v: '7', l: '7 - PERMISSION_DENIED' },
          { v: '8', l: '8 - RESOURCE_EXHAUSTED' }, { v: '13', l: '13 - INTERNAL' },
          { v: '14', l: '14 - UNAVAILABLE' }, { v: '15', l: '15 - DATA_LOSS' },
          { v: '16', l: '16 - UNAUTHENTICATED' }
        ]},
        { key: 'grpc_message', label: 'Error Message', type: 'text', value: 'Service Unavailable (faultbox chaos)' }
      ],
      tls_fault: [
        { key: 'mode', label: 'Fault Mode', type: 'select', value: 'alert_handshake_failure', options: [
          'alert_handshake_failure', 'alert_bad_certificate', 'alert_access_denied', 'stall_handshake', 'corrupt_handshake'
        ]},
        { key: 'stall_seconds', label: 'Stall Duration (sec)', type: 'number', value: 30.0, min: 0.1, step: 0.1 }
      ]
    };

    /* ── Toast system ── */
    function toast(message, type = 'success') {
      const container = document.getElementById('toast-container');
      const el = document.createElement('div');
      const icon = type === 'success' ? '✓' : '✗';
      el.className = 'toast toast-' + type;
      el.innerHTML = '<span class="toast-icon">' + icon + '</span>' + message;
      container.appendChild(el);
      setTimeout(() => el.remove(), 4000);
    }

    /* ── Confirm dialog ── */
    function confirmAction(title, message, sub, callback) {
      document.getElementById('confirm-title').textContent = title;
      document.getElementById('confirm-message').textContent = message;
      document.getElementById('confirm-sub').textContent = sub || '';
      const btn = document.getElementById('confirm-action-btn');
      btn.onclick = () => { closeModal('modal-confirm'); callback(); };
      openModal('modal-confirm');
    }

    /* ── Modal management ── */
    function openModal(id) { document.getElementById(id).classList.add('active'); }
    function closeModal(id) { document.getElementById(id).classList.remove('active'); }

    // Close modals on overlay click
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
      }
    });
    // Close modals on Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
      }
    });

    /* ── Dynamic form fields ── */
    function updateToxicFields() {
      const type = document.getElementById('toxic-type').value;
      const container = document.getElementById('toxic-dynamic-fields');
      const fields = toxicFieldDefs[type] || [];

      container.innerHTML = fields.map(f => {
        let inputHtml = '';
        if (f.type === 'select') {
          const opts = f.options.map(o => {
            if (typeof o === 'object') return '<option value="' + o.v + '"' + (o.v === String(f.value) ? ' selected' : '') + '>' + o.l + '</option>';
            return '<option value="' + o + '"' + (o === f.value ? ' selected' : '') + '>' + o + '</option>';
          }).join('');
          inputHtml = '<select data-field="' + f.key + '">' + opts + '</select>';
        } else if (f.type === 'number') {
          const step = f.step || (String(f.value).includes('.') ? '0.1' : '1');
          inputHtml = '<input type="number" data-field="' + f.key + '" value="' + f.value + '"'
            + (f.min !== undefined ? ' min="' + f.min + '"' : '')
            + (f.max !== undefined ? ' max="' + f.max + '"' : '')
            + ' step="' + step + '">';
        } else {
          inputHtml = '<input type="text" data-field="' + f.key + '" value="' + f.value.replace(/"/g, '&quot;') + '">';
        }
        return '<div class="form-group"><label>' + f.label + '</label>' + inputHtml + '</div>';
      }).join('');

      // Sync to raw JSON
      syncFieldsToJson();
    }

    function syncFieldsToJson() {
      const type = document.getElementById('toxic-type').value;
      const fields = toxicFieldDefs[type] || [];
      const attrs = {};
      fields.forEach(f => {
        const el = document.querySelector('[data-field="' + f.key + '"]');
        if (!el) return;
        if (f.type === 'number') {
          attrs[f.key] = parseFloat(el.value) || 0;
        } else {
          attrs[f.key] = el.value;
        }
      });
      document.getElementById('toxic-attributes').value = JSON.stringify(attrs, null, 2);
    }

    // Listen for field changes to sync JSON
    document.getElementById('toxic-dynamic-fields').addEventListener('input', syncFieldsToJson);
    document.getElementById('toxic-dynamic-fields').addEventListener('change', syncFieldsToJson);

    function toggleAdvancedJson() {
      const el = document.getElementById('toxic-advanced-json');
      el.style.display = el.style.display === 'none' ? 'block' : 'none';
    }

    /* ── Sparkline rendering ── */
    const sparkData = {
      proxies: [], conn: [], inRate: [], outRate: [], errors: []
    };
    const SPARK_MAX = 40;

    function pushSpark(arr, val) {
      arr.push(val);
      if (arr.length > SPARK_MAX) arr.shift();
    }

    function drawSparkline(canvasId, data, color) {
      const canvas = document.getElementById(canvasId);
      if (!canvas || !data.length) return;
      const ctx = canvas.getContext('2d');
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, rect.width, rect.height);

      const max = Math.max(...data, 1);
      const stepX = rect.width / (SPARK_MAX - 1);
      const h = rect.height;

      ctx.beginPath();
      ctx.moveTo(0, h);
      data.forEach((v, i) => {
        const x = i * stepX;
        const y = h - (v / max) * h * 0.85;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });

      // Fill area under curve
      ctx.lineTo((data.length - 1) * stepX, h);
      ctx.lineTo(0, h);
      ctx.closePath();
      const grad = ctx.createLinearGradient(0, 0, 0, h);
      grad.addColorStop(0, color);
      grad.addColorStop(1, 'transparent');
      ctx.fillStyle = grad;
      ctx.fill();

      // Stroke line
      ctx.beginPath();
      data.forEach((v, i) => {
        const x = i * stepX;
        const y = h - (v / max) * h * 0.85;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }

    /* ── Format bytes ── */
    function fmtBytes(bytes) {
      if (bytes < 1024) return bytes.toFixed(0) + ' B';
      if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
      return (bytes / 1048576).toFixed(2) + ' MB';
    }

    function fmtRate(kbps) {
      if (kbps < 1) return (kbps * 1024).toFixed(0) + ' B/s';
      if (kbps < 1024) return kbps.toFixed(1) + ' KB/s';
      return (kbps / 1024).toFixed(2) + ' MB/s';
    }

    /* ── Fetch and render ── */
    async function fetchProxies() {
      try {
        const resp = await fetch('/proxies');
        if (!resp.ok) return;
        const proxies = await resp.json();
        renderProxies(proxies);
      } catch (err) {
        console.error('Failed fetching proxies:', err);
      }
    }

    function renderProxies(proxies) {
      const tbody = document.getElementById('proxy-table-body');
      if (!proxies.length) {
        tbody.innerHTML = '<tr><td colspan="7"><div class="empty-state">'
          + '<svg width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round"/></svg>'
          + '<p>No proxies registered yet.<br>Click <strong>New Proxy</strong> to create one.</p>'
          + '</div></td></tr>';
      } else {
        tbody.innerHTML = proxies.map(p => {
          const statusBadge = p.enabled
            ? '<span class="badge badge-green">Active</span>'
            : '<span class="badge badge-yellow">Paused</span>';

          const toxicsHtml = p.toxics.length
            ? p.toxics.map(t =>
                '<span class="toxic-tag toxic-' + t.type + '">'
                + t.name + ' <span style="opacity:0.6">(' + t.type + ')</span> '
                + '<span class="toxic-delete" onclick="removeToxic(\\'' + p.name + '\\', \\'' + t.name + '\\')">&times;</span>'
                + '</span>'
              ).join(' ')
            : '<span class="pristine-tag">Clean</span>';

          const bytesIn = fmtBytes(p.stats.bytes_in);
          const bytesOut = fmtBytes(p.stats.bytes_out);

          const toggleFn = p.enabled ? 'pauseProxy' : 'resumeProxy';
          const toggleLabel = p.enabled ? 'Pause' : 'Resume';
          const toggleIcon = p.enabled
            ? '<svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16"><rect x="3" y="2" width="3.5" height="12" rx="1"/><rect x="9.5" y="2" width="3.5" height="12" rx="1"/></svg>'
            : '<svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16"><path d="M4 2l10 6-10 6V2z"/></svg>';

          return '<tr>'
            + '<td style="font-weight:600;color:var(--text-bright)">' + p.name + '</td>'
            + '<td><code>' + p.listen + '</code></td>'
            + '<td><code>' + p.upstream + '</code></td>'
            + '<td>' + statusBadge + '</td>'
            + '<td>' + toxicsHtml + '</td>'
            + '<td style="font-size:12px;font-family:var(--mono);white-space:nowrap">' + bytesIn + ' ↓ / ' + bytesOut + ' ↑</td>'
            + '<td><div class="proxy-actions">'
              + '<button class="btn btn-sm" onclick="openAddToxicModal(\\'' + p.name + '\\')" title="Add Toxic">+ Toxic</button>'
              + '<button class="btn btn-sm btn-icon" onclick="' + toggleFn + '(\\'' + p.name + '\\')" title="' + toggleLabel + '">' + toggleIcon + '</button>'
              + '<button class="btn btn-sm" onclick="resetProxy(\\'' + p.name + '\\')" title="Reset">Reset</button>'
              + '<button class="btn btn-sm btn-icon btn-danger" onclick="deleteProxy(\\'' + p.name + '\\')" title="Delete">'
              + '<svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 16 16"><path d="M2 4h12M5 4V2.5A1.5 1.5 0 016.5 1h3A1.5 1.5 0 0111 2.5V4m1 0v9a1.5 1.5 0 01-1.5 1.5h-5A1.5 1.5 0 014 13V4" stroke-linecap="round"/></svg>'
              + '</button>'
            + '</div></td>'
          + '</tr>';
        }).join('');
      }

      // Update KPIs
      const proxyCount = proxies.length;
      const connActive = proxies.reduce((a, p) => a + (p.stats.connections_active || 0), 0);
      const totalInKbps = proxies.reduce((a, p) => a + (p.stats.throughput_in_kbps || 0), 0);
      const totalOutKbps = proxies.reduce((a, p) => a + (p.stats.throughput_out_kbps || 0), 0);
      const totalErrors = proxies.reduce((a, p) => a + (p.stats.errors_total || 0), 0);

      document.getElementById('kpi-proxies').textContent = proxyCount;
      document.getElementById('kpi-conn-active').textContent = connActive;
      document.getElementById('kpi-throughput-in').textContent = fmtRate(totalInKbps);
      document.getElementById('kpi-throughput-out').textContent = fmtRate(totalOutKbps);
      document.getElementById('kpi-errors').textContent = totalErrors;

      // Push sparkline data
      pushSpark(sparkData.proxies, proxyCount);
      pushSpark(sparkData.conn, connActive);
      pushSpark(sparkData.inRate, totalInKbps);
      pushSpark(sparkData.outRate, totalOutKbps);
      pushSpark(sparkData.errors, totalErrors);

      drawSparkline('spark-proxies', sparkData.proxies, '#3b82f6');
      drawSparkline('spark-conn', sparkData.conn, '#22c55e');
      drawSparkline('spark-in', sparkData.inRate, '#06b6d4');
      drawSparkline('spark-out', sparkData.outRate, '#a855f7');
      drawSparkline('spark-errors', sparkData.errors, '#ef4444');
    }

    /* ── Proxy CRUD ── */
    async function pauseProxy(name) {
      await fetch('/proxies/' + name + '/pause', { method: 'POST' });
      toast('Proxy "' + name + '" paused');
      fetchProxies();
    }
    async function resumeProxy(name) {
      await fetch('/proxies/' + name + '/resume', { method: 'POST' });
      toast('Proxy "' + name + '" resumed');
      fetchProxies();
    }
    async function resetProxy(name) {
      confirmAction('Reset Proxy', 'Remove all toxics from "' + name + '"?', 'Traffic will flow through without any chaos injection.', async () => {
        await fetch('/proxies/' + name + '/reset', { method: 'POST' });
        toast('All toxics cleared from "' + name + '"');
        fetchProxies();
      });
    }
    async function deleteProxy(name) {
      confirmAction('Delete Proxy', 'Permanently delete proxy "' + name + '"?', 'All active connections will be terminated.', async () => {
        await fetch('/proxies/' + name, { method: 'DELETE' });
        toast('Proxy "' + name + '" deleted');
        fetchProxies();
      });
    }
    async function removeToxic(proxy, toxic) {
      await fetch('/proxies/' + proxy + '/toxics/' + toxic, { method: 'DELETE' });
      toast('Toxic "' + toxic + '" removed');
      fetchProxies();
    }

    function openAddToxicModal(proxy) {
      document.getElementById('toxic-target-proxy').textContent = proxy;
      document.getElementById('toxic-proxy-name').value = proxy;
      document.getElementById('toxic-name').value = 'toxic-' + Math.random().toString(36).substring(2, 7);
      document.getElementById('toxic-probability').value = 1.0;
      document.getElementById('toxic-prob-display').textContent = '100%';
      document.getElementById('toxic-type').value = 'latency';
      document.getElementById('toxic-advanced-json').style.display = 'none';
      updateToxicFields();
      openModal('modal-toxic');
    }

    async function submitCreateProxy() {
      const name = document.getElementById('new-proxy-name').value.trim();
      const listen = document.getElementById('new-proxy-listen').value.trim();
      const upstream = document.getElementById('new-proxy-upstream').value.trim();
      if (!name || !listen || !upstream) { toast('Please fill in all fields', 'error'); return; }

      try {
        const res = await fetch('/proxies', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, listen, upstream })
        });
        if (res.ok) {
          closeModal('modal-proxy');
          document.getElementById('new-proxy-name').value = '';
          document.getElementById('new-proxy-listen').value = '';
          document.getElementById('new-proxy-upstream').value = '';
          toast('Proxy "' + name + '" created');
          fetchProxies();
        } else {
          const err = await res.json();
          toast(err.detail || 'Failed to create proxy', 'error');
        }
      } catch (e) {
        toast('Connection error', 'error');
      }
    }

    async function submitAddToxic() {
      const proxy = document.getElementById('toxic-proxy-name').value;
      const name = document.getElementById('toxic-name').value.trim();
      const type = document.getElementById('toxic-type').value;
      const direction = document.getElementById('toxic-direction').value;
      const toxicity = parseFloat(document.getElementById('toxic-probability').value) || 1.0;

      // Sync fields to JSON first
      syncFieldsToJson();

      let attributes = {};
      try {
        attributes = JSON.parse(document.getElementById('toxic-attributes').value);
      } catch(e) {
        toast('Invalid JSON in attributes', 'error');
        return;
      }

      // Convert numeric string values from selects (e.g., grpc_status, status_code)
      if (attributes.grpc_status !== undefined) attributes.grpc_status = parseInt(attributes.grpc_status);
      if (attributes.status_code !== undefined) attributes.status_code = parseInt(attributes.status_code);

      try {
        const res = await fetch('/proxies/' + proxy + '/toxics', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, type, direction, toxicity, attributes })
        });
        if (res.ok) {
          closeModal('modal-toxic');
          toast('Toxic "' + name + '" attached to "' + proxy + '"');
          fetchProxies();
        } else {
          const err = await res.json();
          toast(err.detail || 'Failed to attach toxic', 'error');
        }
      } catch (e) {
        toast('Connection error', 'error');
      }
    }

    /* ── WebSocket telemetry with reconnection ── */
    let wsReconnectTimer = null;
    let wsReconnectAttempts = 0;

    function initTelemetry() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(protocol + '//' + window.location.host + '/ws/telemetry');

      ws.onopen = () => {
        wsReconnectAttempts = 0;
        const badge = document.getElementById('conn-status');
        badge.textContent = 'Live Feed';
        badge.className = 'badge badge-green';
      };

      ws.onmessage = (event) => {
        try {
          const proxies = JSON.parse(event.data);
          renderProxies(proxies);
        } catch (e) {}
      };

      ws.onclose = () => {
        const badge = document.getElementById('conn-status');
        badge.textContent = 'Reconnecting';
        badge.className = 'badge badge-yellow';

        // Exponential backoff reconnection (max 30s)
        const delay = Math.min(1000 * Math.pow(1.5, wsReconnectAttempts), 30000);
        wsReconnectAttempts++;
        wsReconnectTimer = setTimeout(initTelemetry, delay);
      };

      ws.onerror = () => ws.close();
    }

    /* ── Init ── */
    fetchProxies();
    initTelemetry();
  </script>
</body>
</html>
"""
