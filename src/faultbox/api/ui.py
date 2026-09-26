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
        <img class="header-logo" src="data:image/png;base64,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" alt="FaultBox Logo" style="border-radius: 10px;">
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
