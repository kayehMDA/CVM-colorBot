const API = "/api/v1";

const SECTION_META = {
  general: { endpoint: "general", title: "--enable General", hasState: true },
  "main-aimbot": { endpoint: "main-aimbot", title: "--enable Main Aimbot", hasState: true },
  "sec-aimbot": { endpoint: "sec-aimbot", title: "--enable Sec Aimbot", hasState: true },
  trigger: { endpoint: "trigger", title: "--enable Trigger", hasState: true },
  rcs: { endpoint: "rcs", title: "--enable RCS", hasState: true },
  config: { endpoint: null, title: "--enable Config", hasState: false },
};

const FIELD_MAP = {
  general: [
    ["color", "select"],
    ["capture_mode", "select"],
    ["target_fps", "range-num-int"],
  ],
  "main-aimbot": [
    ["enableaim", "checkbox"],
    ["mode", "select"],
    ["fovsize", "range-num-int"],
    ["normal_x_speed", "range-num-float"],
    ["normal_y_speed", "range-num-float"],
    ["normalsmooth", "range-num-int"],
    ["ads_fov_enabled", "checkbox"],
    ["ads_fovsize", "range-num-int"],
    ["aim_type", "select"],
  ],
  "sec-aimbot": [
    ["enableaim_sec", "checkbox"],
    ["mode_sec", "select"],
    ["fovsize_sec", "range-num-int"],
    ["normal_x_speed_sec", "range-num-float"],
    ["normal_y_speed_sec", "range-num-float"],
    ["normalsmooth_sec", "range-num-int"],
    ["ads_fov_enabled_sec", "checkbox"],
    ["ads_fovsize_sec", "range-num-int"],
    ["aim_type_sec", "select"],
  ],
  trigger: [
    ["enabletb", "checkbox"],
    ["trigger_type", "select"],
    ["tbfovsize", "range-num-int"],
    ["tbdelay_min", "range-num-float"],
    ["tbdelay_max", "range-num-float"],
    ["trigger_roi_size", "range-num-int"],
    ["trigger_min_pixels", "range-num-int"],
    ["trigger_min_ratio", "range-num-float"],
    ["trigger_ads_fov_enabled", "checkbox"],
    ["trigger_ads_fovsize", "range-num-int"],
  ],
  rcs: [
    ["enablercs", "checkbox"],
    ["rcs_pull_speed", "range-num-int"],
    ["rcs_activation_delay", "range-num-int"],
    ["rcs_rapid_click_threshold", "range-num-int"],
    ["rcs_release_y_enabled", "checkbox"],
    ["rcs_release_y_duration", "range-num-float"],
  ],
  config: [],
};

const brandVersion = document.getElementById("brand-version");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const saveBtn = document.getElementById("save-btn");
const panelTitle = document.getElementById("panel-title");
const navItems = [...document.querySelectorAll(".nav-item")];
const savedConfigSelect = document.getElementById("saved_config_select");
const loadConfigBtn = document.getElementById("load_config_btn");
const saveNewConfigBtn = document.getElementById("save_new_config_btn");
const refreshConfigsBtn = document.getElementById("refresh_configs_btn");
const newConfigNameInput = document.getElementById("new_config_name");
const configActionStatus = document.getElementById("config_action_status");

let pollMs = 750;
let currentTab = "general";
let suppressChange = false;
const debounceTimers = {};
const latestState = {};

function getEl(id) {
  return document.getElementById(id);
}

async function fetchJson(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.message || data.error || `HTTP ${res.status}`);
  return data;
}

function setConnected(connected) {
  statusDot.classList.toggle("offline", !connected);
  statusText.textContent = connected ? "Connected" : "Offline";
}

function switchTab(tabId) {
  currentTab = tabId;
  navItems.forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === tabId));
  document.querySelectorAll(".tab-content").forEach((el) => el.classList.remove("active"));
  getEl(`tab-${tabId}`).classList.add("active");
  panelTitle.textContent = SECTION_META[tabId].title;
}

function applyStateToSection(section, data) {
  latestState[section] = data;
  suppressChange = true;
  for (const [key, type] of FIELD_MAP[section]) {
    const el = getEl(key);
    if (!el || !(key in data)) continue;
    const value = data[key];
    if (type === "checkbox") {
      el.checked = !!value;
    } else if (type === "select") {
      el.value = String(value);
    } else if (type.startsWith("range-num")) {
      const numEl = getEl(`${key}_num`);
      el.value = String(value);
      if (numEl) numEl.value = String(value);
    }
  }
  if (data.connected && typeof data.connected.overall === "boolean") {
    setConnected(!!data.connected.overall);
  }
  suppressChange = false;
}

function debouncePatch(section, payload, delay = 200) {
  const id = `${section}:${Object.keys(payload).join(",")}`;
  if (debounceTimers[id]) clearTimeout(debounceTimers[id]);
  debounceTimers[id] = setTimeout(() => patchSection(section, payload), delay);
}

async function patchSection(section, payload) {
  try {
    const state = await fetchJson(`${API}/state/${SECTION_META[section].endpoint}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    applyStateToSection(section, state);
  } catch (err) {
    console.error("PATCH failed", section, err.message);
  }
}

function bindSectionEvents(section) {
  for (const [key, type] of FIELD_MAP[section]) {
    const el = getEl(key);
    if (!el) continue;

    if (type === "checkbox") {
      el.addEventListener("change", () => {
        if (suppressChange) return;
        patchSection(section, { [key]: !!el.checked });
      });
    } else if (type === "select") {
      el.addEventListener("change", () => {
        if (suppressChange) return;
        patchSection(section, { [key]: el.value });
      });
    } else if (type.startsWith("range-num")) {
      const isFloat = type.endsWith("float");
      const numEl = getEl(`${key}_num`);
      el.addEventListener("input", () => {
        if (numEl) numEl.value = el.value;
        if (suppressChange) return;
        const value = isFloat ? parseFloat(el.value) : parseInt(el.value, 10);
        debouncePatch(section, { [key]: value }, 200);
      });
      if (numEl) {
        numEl.addEventListener("change", () => {
          el.value = numEl.value;
          if (suppressChange) return;
          const value = isFloat ? parseFloat(numEl.value) : parseInt(numEl.value, 10);
          patchSection(section, { [key]: value });
        });
      }
    }
  }
}

async function refreshAllStates() {
  for (const section of Object.keys(SECTION_META)) {
    if (!SECTION_META[section].hasState) continue;
    try {
      const data = await fetchJson(`${API}/state/${SECTION_META[section].endpoint}`);
      applyStateToSection(section, data);
    } catch (err) {
      setConnected(false);
    }
  }
}

function setConfigStatus(text, isError = false) {
  configActionStatus.textContent = text;
  configActionStatus.style.color = isError ? "#ff4d6d" : "";
}

async function refreshConfigsList() {
  try {
    const data = await fetchJson(`${API}/configs`);
    const cfgs = Array.isArray(data.configs) ? data.configs : [];
    const current = savedConfigSelect.value;
    savedConfigSelect.innerHTML = "";
    for (const name of cfgs) {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      savedConfigSelect.appendChild(opt);
    }
    if (cfgs.includes(current)) {
      savedConfigSelect.value = current;
    }
    setConfigStatus(`Loaded ${cfgs.length} config(s).`);
  } catch (err) {
    setConfigStatus(`Failed to list configs: ${err.message}`, true);
  }
}

async function loadSelectedConfig() {
  const name = String(savedConfigSelect.value || "").trim();
  if (!name) {
    setConfigStatus("Select a config first.", true);
    return;
  }
  try {
    await fetchJson(`${API}/configs/load`, {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    setConfigStatus(`Loaded config: ${name}`);
    await refreshAllStates();
  } catch (err) {
    setConfigStatus(`Load failed: ${err.message}`, true);
  }
}

async function saveNewConfig() {
  const name = String(newConfigNameInput.value || "").trim();
  if (!name) {
    setConfigStatus("Enter a config name.", true);
    return;
  }
  try {
    const data = await fetchJson(`${API}/configs/save-new`, {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    setConfigStatus(`Saved new config: ${data.name}`);
    newConfigNameInput.value = "";
    await refreshConfigsList();
  } catch (err) {
    setConfigStatus(`Save failed: ${err.message}`, true);
  }
}

async function saveConfig() {
  try {
    await fetchJson(`${API}/actions/save-config`, { method: "POST", body: "{}" });
    saveBtn.textContent = "SYNCED";
    setTimeout(() => (saveBtn.textContent = "SYNC"), 900);
  } catch {
    saveBtn.textContent = "ERROR";
    setTimeout(() => (saveBtn.textContent = "SYNC"), 1200);
  }
}

async function boot() {
  try {
    const meta = await fetchJson(`${API}/meta`);
    brandVersion.textContent = `v${meta.version || "unknown"}`;
    pollMs = Number(meta.poll_ms) || 750;
  } catch {
    brandVersion.textContent = "v?";
  }

  Object.keys(SECTION_META).forEach(bindSectionEvents);

  navItems.forEach((btn) =>
    btn.addEventListener("click", () => switchTab(btn.dataset.tab))
  );
  saveBtn.addEventListener("click", saveConfig);
  loadConfigBtn.addEventListener("click", loadSelectedConfig);
  saveNewConfigBtn.addEventListener("click", saveNewConfig);
  refreshConfigsBtn.addEventListener("click", refreshConfigsList);

  switchTab("general");
  await refreshAllStates();
  await refreshConfigsList();
  setInterval(refreshAllStates, pollMs);
}

boot();
