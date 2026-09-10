"""Embedded single-page Web UI dashboard for FaultBox."""

from __future__ import annotations


def get_ui_html() -> str:
    """Return standalone HTML5 application for the browser dashboard."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FaultBox Control Dashboard</title>
  <style>
    :root {
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --text-muted: #8b949e;
      --accent: #58a6ff;
      --green: #3fb950;
      --red: #f85149;
      --yellow: #d29922;
      --purple: #bc8cff;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.5;
      padding: 24px;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border);
      padding-bottom: 16px;
      margin-bottom: 24px;
    }
    h1 { font-size: 22px; font-weight: 600; color: #fff; }
    .subtitle { color: var(--text-muted); font-size: 13px; margin-top: 4px; }
    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
    }
    .badge-green { background: rgba(63, 185, 80, 0.15); color: var(--green); border: 1px solid var(--green); }
    .badge-red { background: rgba(248, 81, 73, 0.15); color: var(--red); border: 1px solid var(--red); }
    .badge-yellow { background: rgba(210, 153, 34, 0.15); color: var(--yellow); border: 1px solid var(--yellow); }

    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .kpi-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
    }
    .kpi-title { font-size: 12px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; }
    .kpi-value { font-size: 24px; font-weight: 700; color: #fff; margin-top: 6px; }

    .panel {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
      margin-bottom: 24px;
    }
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 14px 18px;
      border-bottom: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.02);
    }
    .panel-title { font-weight: 600; font-size: 15px; color: #fff; }

    table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
    th { background: rgba(255, 255, 255, 0.03); color: var(--text-muted); padding: 10px 16px; border-bottom: 1px solid var(--border); font-weight: 600; }
    td { padding: 12px 16px; border-bottom: 1px solid var(--border); vertical-align: middle; }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: rgba(255, 255, 255, 0.015); }

    .btn {
      background: #21262d;
      color: var(--text);
      border: 1px solid var(--border);
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 500;
      transition: background 0.15s ease;
    }
    .btn:hover { background: #30363d; }
    .btn-primary { background: #238636; color: #fff; border-color: rgba(240,246,252,0.1); }
    .btn-primary:hover { background: #2ea043; }
    .btn-danger { background: rgba(248, 81, 73, 0.1); color: var(--red); border-color: var(--red); }
    .btn-danger:hover { background: rgba(248, 81, 73, 0.25); }

    .toxic-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(248, 81, 73, 0.12);
      border: 1px solid rgba(248, 81, 73, 0.3);
      color: #ff7b72;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 11px;
      margin: 2px;
    }
    .toxic-delete { cursor: pointer; font-weight: bold; }
    .toxic-delete:hover { color: #fff; }

    /* Modal */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.65);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 100;
    }
    .modal {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      width: 100%;
      max-width: 480px;
      padding: 20px;
    }
    .modal-title { font-size: 16px; font-weight: 600; color: #fff; margin-bottom: 14px; }
    .form-group { margin-bottom: 14px; }
    label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
    input, select, textarea {
      width: 100%;
      background: #0d1117;
      border: 1px solid var(--border);
      color: #fff;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 13px;
      font-family: inherit;
    }
    input:focus, select:focus, textarea:focus { outline: none; border-color: var(--accent); }
    .modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 18px; }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>FaultBox Control Dashboard</h1>
      <div class="subtitle">Programmable Network & Protocol Chaos Injection Proxy</div>
    </div>
    <div style="display: flex; gap: 8px; align-items: center;">
      <span id="conn-status" class="badge badge-green">Live Feed</span>
      <button class="btn btn-primary" onclick="openCreateProxyModal()">New Proxy</button>
    </div>
  </header>

  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-title">Active Proxies</div>
      <div class="kpi-value" id="kpi-proxies">0</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Active Connections</div>
      <div class="kpi-value" id="kpi-conn-active">0</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Throughput In</div>
      <div class="kpi-value" id="kpi-throughput-in">0.0 KB/s</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Throughput Out</div>
      <div class="kpi-value" id="kpi-throughput-out">0.0 KB/s</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Total Errors</div>
      <div class="kpi-value" id="kpi-errors">0</div>
    </div>
  </div>

  <div class="panel">
    <div class="panel-header">
      <span class="panel-title">Active Chaos Proxies</span>
      <button class="btn" onclick="fetchProxies()">Refresh</button>
    </div>
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Listening On</th>
          <th>Upstream Destination</th>
          <th>State</th>
          <th>Active Toxics</th>
          <th>Transferred</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody id="proxy-table-body">
        <tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Loading proxies...</td></tr>
      </tbody>
    </table>
  </div>

  <!-- Create Proxy Modal -->
  <div class="modal-overlay" id="modal-proxy">
    <div class="modal">
      <div class="modal-title">Create New Proxy Route</div>
      <div class="form-group">
        <label>Proxy Name</label>
        <input type="text" id="new-proxy-name" placeholder="e.g. order-db">
      </div>
      <div class="form-group">
        <label>Listen Address / Port</label>
        <input type="text" id="new-proxy-listen" placeholder="0.0.0.0:9000 or 9000">
      </div>
      <div class="form-group">
        <label>Upstream Host / Port</label>
        <input type="text" id="new-proxy-upstream" placeholder="127.0.0.1:5432">
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
      <div class="modal-title">Attach Chaos Toxic to <span id="toxic-target-proxy" style="color: var(--accent);"></span></div>
      <input type="hidden" id="toxic-proxy-name">
      <div class="form-group">
        <label>Toxic Name</label>
        <input type="text" id="toxic-name" placeholder="e.g. latency-spike">
      </div>
      <div class="form-group">
        <label>Toxic Type</label>
        <select id="toxic-type" onchange="updateToxicTemplate()">
          <option value="latency">Latency</option>
          <option value="waveform_latency">Waveform Latency</option>
          <option value="bandwidth">Bandwidth Throttling</option>
          <option value="reset_peer">Reset Peer (TCP RST)</option>
          <option value="timeout">Timeout / Hang</option>
          <option value="corrupt">Byte Corruption</option>
          <option value="slicer">Packet Slicer</option>
          <option value="flapping">Flapping Connection</option>
          <option value="http_error">HTTP Error Status</option>
        </select>
      </div>
      <div class="form-group">
        <label>Direction</label>
        <select id="toxic-direction">
          <option value="both">Both Directions</option>
          <option value="inbound">Inbound (Client -> Upstream)</option>
          <option value="outbound">Outbound (Upstream -> Client)</option>
        </select>
      </div>
      <div class="form-group">
        <label>Toxicity Probability (0.0 to 1.0)</label>
        <input type="number" id="toxic-probability" min="0" max="1" step="0.1" value="1.0">
      </div>
      <div class="form-group">
        <label>Attributes (JSON)</label>
        <textarea id="toxic-attributes" rows="4">{"latency_ms": 250, "jitter_ms": 50}</textarea>
      </div>
      <div class="modal-actions">
        <button class="btn" onclick="closeModal('modal-toxic')">Cancel</button>
        <button class="btn btn-primary" onclick="submitAddToxic()">Attach Toxic</button>
      </div>
    </div>
  </div>

  <script>
    const templates = {
      latency: { latency_ms: 250, jitter_ms: 50, distribution: "uniform" },
      waveform_latency: { base_latency_ms: 100, amplitude_ms: 300, period_sec: 15.0, waveform: "sine" },
      bandwidth: { rate_kbps: 50 },
      reset_peer: { byte_offset: 1024, timeout_ms: 0 },
      timeout: { timeout_ms: 2000 },
      corrupt: { rate: 0.05, mode: "bitflip" },
      slicer: { slice_size: 64, delay_ms: 10 },
      flapping: { up_duration_sec: 8.0, down_duration_sec: 4.0, down_action: "reset" },
      http_error: { status_code: 503, status_message: "Service Unavailable", body: "{\\"error\\":\\"Service Unavailable\\"}" }
    };

    function updateToxicTemplate() {
      const type = document.getElementById("toxic-type").value;
      document.getElementById("toxic-attributes").value = JSON.stringify(templates[type] || {}, null, 2);
    }

    async function fetchProxies() {
      try {
        const resp = await fetch("/proxies");
        if (!resp.ok) return;
        const proxies = await resp.json();
        renderProxies(proxies);
      } catch (err) {
        console.error("Failed fetching proxies:", err);
      }
    }

    function renderProxies(proxies) {
      const tbody = document.getElementById("proxy-table-body");
      if (!proxies.length) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No proxies registered yet. Click New Proxy above.</td></tr>';
      } else {
        tbody.innerHTML = proxies.map(p => {
          const statusBadge = p.enabled ? '<span class="badge badge-green">ACTIVE</span>' : '<span class="badge badge-yellow">PAUSED</span>';
          const toxicsHtml = p.toxics.length
            ? p.toxics.map(t => `<span class="toxic-tag">${t.name} (${t.type}) <span class="toxic-delete" onclick="removeToxic('${p.name}', '${t.name}')">&times;</span></span>`).join(" ")
            : '<span style="color: var(--green); font-size: 12px;">Pristine</span>';

          const bytesIn = (p.stats.bytes_in / 1024).toFixed(1);
          const bytesOut = (p.stats.bytes_out / 1024).toFixed(1);
          const toggleAction = p.enabled ? `pauseProxy('${p.name}')` : `resumeProxy('${p.name}')`;
          const toggleLabel = p.enabled ? 'Pause' : 'Resume';

          return `<tr>
            <td style="font-weight: 600; color: #fff;">${p.name}</td>
            <td><code>${p.listen}</code></td>
            <td><code>${p.upstream}</code></td>
            <td>${statusBadge}</td>
            <td>${toxicsHtml}</td>
            <td style="font-size: 12px;">${bytesIn} KB in / ${bytesOut} KB out</td>
            <td style="display: flex; gap: 6px;">
              <button class="btn" onclick="openAddToxicModal('${p.name}')">+ Toxic</button>
              <button class="btn" onclick="${toggleAction}">${toggleLabel}</button>
              <button class="btn" onclick="resetProxy('${p.name}')">Reset</button>
              <button class="btn btn-danger" onclick="deleteProxy('${p.name}')">&times;</button>
            </td>
          </tr>`;
        }).join("");
      }

      // Update KPIs
      document.getElementById("kpi-proxies").textContent = proxies.length;
      document.getElementById("kpi-conn-active").textContent = proxies.reduce((acc, p) => acc + (p.stats.connections_active || 0), 0);
      const totalInKbps = proxies.reduce((acc, p) => acc + (p.stats.throughput_in_kbps || 0), 0);
      const totalOutKbps = proxies.reduce((acc, p) => acc + (p.stats.throughput_out_kbps || 0), 0);
      document.getElementById("kpi-throughput-in").textContent = totalInKbps.toFixed(1) + " KB/s";
      document.getElementById("kpi-throughput-out").textContent = totalOutKbps.toFixed(1) + " KB/s";
      document.getElementById("kpi-errors").textContent = proxies.reduce((acc, p) => acc + (p.stats.errors_total || 0), 0);
    }

    async function pauseProxy(name) { await fetch(`/proxies/${name}/pause`, { method: "POST" }); fetchProxies(); }
    async function resumeProxy(name) { await fetch(`/proxies/${name}/resume`, { method: "POST" }); fetchProxies(); }
    async function resetProxy(name) { await fetch(`/proxies/${name}/reset`, { method: "POST" }); fetchProxies(); }
    async function deleteProxy(name) {
      if (confirm(`Delete proxy '${name}'?`)) {
        await fetch(`/proxies/${name}`, { method: "DELETE" });
        fetchProxies();
      }
    }
    async function removeToxic(proxy, toxic) {
      await fetch(`/proxies/${proxy}/toxics/${toxic}`, { method: "DELETE" });
      fetchProxies();
    }

    function openCreateProxyModal() { document.getElementById("modal-proxy").style.display = "flex"; }
    function openAddToxicModal(proxy) {
      document.getElementById("toxic-target-proxy").textContent = proxy;
      document.getElementById("toxic-proxy-name").value = proxy;
      document.getElementById("toxic-name").value = "toxic-" + Math.random().toString(36).substring(2, 7);
      updateToxicTemplate();
      document.getElementById("modal-toxic").style.display = "flex";
    }
    function closeModal(id) { document.getElementById(id).style.display = "none"; }

    async function submitCreateProxy() {
      const name = document.getElementById("new-proxy-name").value.trim();
      const listen = document.getElementById("new-proxy-listen").value.trim();
      const upstream = document.getElementById("new-proxy-upstream").value.trim();
      if (!name || !listen || !upstream) { alert("Please complete all fields."); return; }

      const res = await fetch("/proxies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, listen, upstream })
      });
      if (res.ok) {
        closeModal("modal-proxy");
        fetchProxies();
      } else {
        const err = await res.json();
        alert(err.detail || "Error creating proxy.");
      }
    }

    async function submitAddToxic() {
      const proxy = document.getElementById("toxic-proxy-name").value;
      const name = document.getElementById("toxic-name").value.trim();
      const type = document.getElementById("toxic-type").value;
      const direction = document.getElementById("toxic-direction").value;
      const toxicity = parseFloat(document.getElementById("toxic-probability").value) || 1.0;
      let attributes = {};
      try { attributes = JSON.parse(document.getElementById("toxic-attributes").value); } catch(e) { alert("Invalid JSON attributes"); return; }

      const res = await fetch(`/proxies/${proxy}/toxics`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, type, direction, toxicity, attributes })
      });
      if (res.ok) {
        closeModal("modal-toxic");
        fetchProxies();
      } else {
        const err = await res.json();
        alert(err.detail || "Error attaching toxic.");
      }
    }

    // Connect WebSocket live feed, fallback to polling
    function initTelemetry() {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const ws = new WebSocket(`${protocol}//${window.location.host}/ws/telemetry`);
      ws.onmessage = (event) => {
        try {
          const proxies = JSON.parse(event.data);
          renderProxies(proxies);
        } catch (e) {}
      };
      ws.onclose = () => {
        document.getElementById("conn-status").textContent = "Polling (2s)";
        document.getElementById("conn-status").className = "badge badge-yellow";
        setInterval(fetchProxies, 2000);
      };
    }

    fetchProxies();
    initTelemetry();
  </script>
</body>
</html>
"""
