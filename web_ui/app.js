const API = "/api/v1";

const SECTION_META = {
  general: { endpoint: "general", title: "--enable General", hasState: true },
  "main-aimbot": { endpoint: "main-aimbot", title: "--enable Main Aimbot", hasState: true },
  "sec-aimbot": { endpoint: "sec-aimbot", title: "--enable Sec Aimbot", hasState: true },
  trigger: { endpoint: "trigger", title: "--enable Trigger", hasState: true },
  rcs: { endpoint: "rcs", title: "--enable RCS", hasState: true },
  "all-options": { endpoint: "full", title: "--enable All Options", hasState: true },
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
    ["anti_smoke_enabled", "checkbox"],
    ["humanized_aim_enabled", "checkbox"],
    ["mode", "select"],
    ["fovsize", "range-num-int"],
    ["normal_x_speed", "range-num-float"],
    ["normal_y_speed", "range-num-float"],
    ["normalsmooth", "range-num-int"],
    ["normalsmoothfov", "range-num-int"],
    ["ads_fov_enabled", "checkbox"],
    ["ads_fovsize", "range-num-int"],
    ["aim_offsetX", "range-num-float"],
    ["aim_offsetY", "range-num-float"],
    ["aim_type", "select"],
    ["selected_mouse_button", "select"],
    ["aimbot_activation_type", "select"],
    ["ads_key", "select"],
    ["ads_key_type", "select"],
    ["silent_distance", "range-num-float"],
    ["silent_delay", "range-num-float"],
    ["silent_move_delay", "range-num-float"],
    ["silent_return_delay", "range-num-float"],
    ["ncaf_alpha", "range-num-float"],
    ["ncaf_snap_boost", "range-num-float"],
    ["ncaf_max_step", "range-num-float"],
    ["ncaf_min_speed_multiplier", "range-num-float"],
    ["ncaf_max_speed_multiplier", "range-num-float"],
    ["ncaf_prediction_interval", "range-num-float"],
    ["ncaf_snap_radius", "range-num-int"],
    ["ncaf_near_radius", "range-num-int"],
    ["wm_gravity", "range-num-float"],
    ["wm_wind", "range-num-float"],
    ["wm_max_step", "range-num-float"],
    ["wm_min_step", "range-num-float"],
    ["wm_min_delay", "range-num-float"],
    ["wm_max_delay", "range-num-float"],
    ["wm_distance_threshold", "range-num-float"],
    ["bezier_segments", "range-num-int"],
    ["bezier_ctrl_x", "range-num-float"],
    ["bezier_ctrl_y", "range-num-float"],
    ["bezier_speed", "range-num-float"],
    ["bezier_delay", "range-num-float"],
  ],
  "sec-aimbot": [
    ["enableaim_sec", "checkbox"],
    ["anti_smoke_enabled_sec", "checkbox"],
    ["humanized_aim_enabled_sec", "checkbox"],
    ["mode_sec", "select"],
    ["fovsize_sec", "range-num-int"],
    ["normal_x_speed_sec", "range-num-float"],
    ["normal_y_speed_sec", "range-num-float"],
    ["normalsmooth_sec", "range-num-int"],
    ["normalsmoothfov_sec", "range-num-int"],
    ["ads_fov_enabled_sec", "checkbox"],
    ["ads_fovsize_sec", "range-num-int"],
    ["aim_offsetX_sec", "range-num-float"],
    ["aim_offsetY_sec", "range-num-float"],
    ["aim_type_sec", "select"],
    ["selected_mouse_button_sec", "select"],
    ["aimbot_activation_type_sec", "select"],
    ["ads_key_sec", "select"],
    ["ads_key_type_sec", "select"],
    ["ncaf_alpha_sec", "range-num-float"],
    ["ncaf_snap_boost_sec", "range-num-float"],
    ["ncaf_max_step_sec", "range-num-float"],
    ["ncaf_min_speed_multiplier_sec", "range-num-float"],
    ["ncaf_max_speed_multiplier_sec", "range-num-float"],
    ["ncaf_prediction_interval_sec", "range-num-float"],
    ["ncaf_snap_radius_sec", "range-num-int"],
    ["ncaf_near_radius_sec", "range-num-int"],
    ["wm_gravity_sec", "range-num-float"],
    ["wm_wind_sec", "range-num-float"],
    ["wm_max_step_sec", "range-num-float"],
    ["wm_min_step_sec", "range-num-float"],
    ["wm_min_delay_sec", "range-num-float"],
    ["wm_max_delay_sec", "range-num-float"],
    ["wm_distance_threshold_sec", "range-num-float"],
    ["bezier_segments_sec", "range-num-int"],
    ["bezier_ctrl_x_sec", "range-num-float"],
    ["bezier_ctrl_y_sec", "range-num-float"],
    ["bezier_speed_sec", "range-num-float"],
    ["bezier_delay_sec", "range-num-float"],
  ],
  trigger: [
    ["enabletb", "checkbox"],
    ["trigger_type", "select"],
    ["tbfovsize", "range-num-int"],
    ["tbdelay_min", "range-num-float"],
    ["tbdelay_max", "range-num-float"],
    ["tbhold_min", "range-num-float"],
    ["tbhold_max", "range-num-float"],
    ["tbcooldown_min", "range-num-float"],
    ["tbcooldown_max", "range-num-float"],
    ["trigger_roi_size", "range-num-int"],
    ["trigger_min_pixels", "range-num-int"],
    ["trigger_min_ratio", "range-num-float"],
    ["trigger_confirm_frames", "range-num-int"],
    ["tbburst_count_min", "range-num-int"],
    ["tbburst_count_max", "range-num-int"],
    ["tbburst_interval_min", "range-num-float"],
    ["tbburst_interval_max", "range-num-float"],
    ["trigger_ads_fov_enabled", "checkbox"],
    ["trigger_ads_fovsize", "range-num-int"],
    ["selected_tb_btn", "select"],
    ["trigger_activation_type", "select"],
    ["trigger_ads_key", "select"],
    ["trigger_ads_key_type", "select"],
    ["trigger_strafe_mode", "select"],
    ["trigger_strafe_auto_lead_ms", "range-num-int"],
    ["trigger_strafe_manual_neutral_ms", "range-num-int"],
    ["rgb_color_profile", "select"],
    ["rgb_custom_r", "range-num-int"],
    ["rgb_custom_g", "range-num-int"],
    ["rgb_custom_b", "range-num-int"],
    ["rgb_tbdelay_min", "range-num-float"],
    ["rgb_tbdelay_max", "range-num-float"],
    ["rgb_tbhold_min", "range-num-float"],
    ["rgb_tbhold_max", "range-num-float"],
    ["rgb_tbcooldown_min", "range-num-float"],
    ["rgb_tbcooldown_max", "range-num-float"],
  ],
  rcs: [
    ["enablercs", "checkbox"],
    ["rcs_pull_speed", "range-num-int"],
    ["rcs_activation_delay", "range-num-int"],
    ["rcs_rapid_click_threshold", "range-num-int"],
    ["rcs_release_y_enabled", "checkbox"],
    ["rcs_release_y_duration", "range-num-float"],
  ],
  "all-options": [],
  config: [],
};

const brandVersion = document.getElementById("brand-version");
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const saveBtn = document.getElementById("save-btn");
const panelTitle = document.getElementById("panel-title");
let navItems = [...document.querySelectorAll(".nav-item")];
const savedConfigSelect = document.getElementById("saved_config_select");
const loadConfigBtn = document.getElementById("load_config_btn");
const saveNewConfigBtn = document.getElementById("save_new_config_btn");
const refreshConfigsBtn = document.getElementById("refresh_configs_btn");
const newConfigNameInput = document.getElementById("new_config_name");
const configActionStatus = document.getElementById("config_action_status");
let allOptionsContainer = document.getElementById("all_options_container");

let pollMs = 750;
let currentTab = "general";
let suppressChange = false;
const debounceTimers = {};
const latestState = {};
const fullOptionEditors = new Map();
const ADS_KEY_OPTIONS = [
  "Right Mouse Button",
  "Left Mouse Button",
  "Middle Mouse Button",
  "Side Mouse 4 Button",
  "Side Mouse 5 Button",
  "LSHIFT",
  "RSHIFT",
  "LCONTROL",
  "RCONTROL",
  "LMENU",
  "RMENU",
  "SPACE",
  "E",
  "Q",
  "F",
  "R",
  "C",
  "V",
  "X",
  "Z",
  "W",
  "A",
  "S",
  "D",
];
const SELECT_OPTIONS = {
  selected_mouse_button: [
    ["0", "Left Mouse Button"],
    ["1", "Right Mouse Button"],
    ["2", "Middle Mouse Button"],
    ["3", "Side Mouse 4"],
    ["4", "Side Mouse 5"],
  ],
  selected_mouse_button_sec: [
    ["0", "Left Mouse Button"],
    ["1", "Right Mouse Button"],
    ["2", "Middle Mouse Button"],
    ["3", "Side Mouse 4"],
    ["4", "Side Mouse 5"],
  ],
  selected_tb_btn: [
    ["0", "Left Mouse Button"],
    ["1", "Right Mouse Button"],
    ["2", "Middle Mouse Button"],
    ["3", "Side Mouse 4"],
    ["4", "Side Mouse 5"],
  ],
  aimbot_activation_type: ["hold_enable", "hold_disable", "toggle", "use_enable"],
  aimbot_activation_type_sec: ["hold_enable", "hold_disable", "toggle", "use_enable"],
  ads_key: ADS_KEY_OPTIONS,
  ads_key_sec: ADS_KEY_OPTIONS,
  ads_key_type: ["hold", "toggle"],
  ads_key_type_sec: ["hold", "toggle"],
  trigger_activation_type: ["hold_enable", "hold_disable", "toggle"],
  trigger_ads_key: ADS_KEY_OPTIONS,
  trigger_ads_key_type: ["hold", "toggle"],
  trigger_strafe_mode: ["off", "auto", "manual_wait"],
  rgb_color_profile: ["red", "yellow", "purple", "custom"],
};
const RANGE_META = {
  aim_offsetX: { min: -100, max: 100, step: 1 },
  aim_offsetY: { min: -100, max: 100, step: 1 },
  silent_distance: { min: 0.1, max: 10, step: 0.1 },
  silent_delay: { min: 0.001, max: 300, step: 0.001 },
  silent_move_delay: { min: 0.001, max: 300, step: 0.001 },
  silent_return_delay: { min: 0.001, max: 300, step: 0.001 },
  ncaf_alpha: { min: 0.1, max: 5, step: 0.01 },
  ncaf_snap_boost: { min: 0.01, max: 2, step: 0.01 },
  ncaf_max_step: { min: 1, max: 200, step: 1 },
  ncaf_min_speed_multiplier: { min: 0.01, max: 1, step: 0.01 },
  ncaf_max_speed_multiplier: { min: 1, max: 20, step: 0.1 },
  ncaf_prediction_interval: { min: 0.001, max: 0.1, step: 0.001 },
  ncaf_snap_radius: { min: 10, max: 500, step: 1 },
  ncaf_near_radius: { min: 5, max: 400, step: 1 },
  wm_gravity: { min: 0.1, max: 30, step: 0.1 },
  wm_wind: { min: 0.1, max: 20, step: 0.1 },
  wm_max_step: { min: 1, max: 100, step: 1 },
  wm_min_step: { min: 0.1, max: 20, step: 0.1 },
  wm_min_delay: { min: 0.0001, max: 0.05, step: 0.0001 },
  wm_max_delay: { min: 0.0001, max: 0.05, step: 0.0001 },
  wm_distance_threshold: { min: 10, max: 200, step: 1 },
  bezier_segments: { min: 1, max: 30, step: 1 },
  bezier_ctrl_x: { min: 0, max: 100, step: 0.1 },
  bezier_ctrl_y: { min: 0, max: 100, step: 0.1 },
  bezier_speed: { min: 0.1, max: 20, step: 0.1 },
  bezier_delay: { min: 0.0001, max: 0.05, step: 0.0001 },
  aim_offsetX_sec: { min: -100, max: 100, step: 1 },
  aim_offsetY_sec: { min: -100, max: 100, step: 1 },
  ncaf_alpha_sec: { min: 0.1, max: 5, step: 0.01 },
  ncaf_snap_boost_sec: { min: 0.01, max: 2, step: 0.01 },
  ncaf_max_step_sec: { min: 1, max: 200, step: 1 },
  ncaf_min_speed_multiplier_sec: { min: 0.01, max: 1, step: 0.01 },
  ncaf_max_speed_multiplier_sec: { min: 1, max: 20, step: 0.1 },
  ncaf_prediction_interval_sec: { min: 0.001, max: 0.1, step: 0.001 },
  ncaf_snap_radius_sec: { min: 10, max: 500, step: 1 },
  ncaf_near_radius_sec: { min: 5, max: 400, step: 1 },
  wm_gravity_sec: { min: 0.1, max: 30, step: 0.1 },
  wm_wind_sec: { min: 0.1, max: 20, step: 0.1 },
  wm_max_step_sec: { min: 1, max: 100, step: 1 },
  wm_min_step_sec: { min: 0.1, max: 20, step: 0.1 },
  wm_min_delay_sec: { min: 0.0001, max: 0.05, step: 0.0001 },
  wm_max_delay_sec: { min: 0.0001, max: 0.05, step: 0.0001 },
  wm_distance_threshold_sec: { min: 10, max: 200, step: 1 },
  bezier_segments_sec: { min: 1, max: 30, step: 1 },
  bezier_ctrl_x_sec: { min: 0, max: 100, step: 0.1 },
  bezier_ctrl_y_sec: { min: 0, max: 100, step: 0.1 },
  bezier_speed_sec: { min: 0.1, max: 20, step: 0.1 },
  bezier_delay_sec: { min: 0.0001, max: 0.05, step: 0.0001 },
  tbhold_min: { min: 5, max: 500, step: 1 },
  tbhold_max: { min: 5, max: 500, step: 1 },
  tbcooldown_min: { min: 0, max: 5, step: 0.01 },
  tbcooldown_max: { min: 0, max: 5, step: 0.01 },
  trigger_confirm_frames: { min: 1, max: 10, step: 1 },
  tbburst_count_min: { min: 1, max: 10, step: 1 },
  tbburst_count_max: { min: 1, max: 10, step: 1 },
  tbburst_interval_min: { min: 0, max: 500, step: 1 },
  tbburst_interval_max: { min: 0, max: 500, step: 1 },
  trigger_strafe_auto_lead_ms: { min: 0, max: 50, step: 1 },
  trigger_strafe_manual_neutral_ms: { min: 0, max: 300, step: 1 },
  rgb_custom_r: { min: 0, max: 255, step: 1 },
  rgb_custom_g: { min: 0, max: 255, step: 1 },
  rgb_custom_b: { min: 0, max: 255, step: 1 },
  rgb_tbdelay_min: { min: 0, max: 1, step: 0.01 },
  rgb_tbdelay_max: { min: 0, max: 1, step: 0.01 },
  rgb_tbhold_min: { min: 5, max: 500, step: 1 },
  rgb_tbhold_max: { min: 5, max: 500, step: 1 },
  rgb_tbcooldown_min: { min: 0, max: 5, step: 0.01 },
  rgb_tbcooldown_max: { min: 0, max: 5, step: 0.01 },
};

const AIMBOT_MODE_FIELDS = {
  "main-aimbot": {
    modeKey: "mode",
    fieldsByMode: {
      Normal: [
        "normal_x_speed",
        "normal_y_speed",
        "normalsmooth",
        "fovsize",
        "normalsmoothfov",
        "ads_fov_enabled",
        "ads_fovsize",
      ],
      Silent: [
        "silent_distance",
        "silent_delay",
        "silent_move_delay",
        "silent_return_delay",
        "fovsize",
        "ads_fov_enabled",
        "ads_fovsize",
      ],
      NCAF: [
        "ncaf_alpha",
        "ncaf_snap_boost",
        "ncaf_max_step",
        "ncaf_min_speed_multiplier",
        "ncaf_max_speed_multiplier",
        "ncaf_prediction_interval",
        "ncaf_snap_radius",
        "ncaf_near_radius",
        "ads_fov_enabled",
        "ads_fovsize",
      ],
      WindMouse: [
        "wm_gravity",
        "wm_wind",
        "wm_max_step",
        "wm_min_step",
        "wm_min_delay",
        "wm_max_delay",
        "wm_distance_threshold",
        "fovsize",
        "ads_fov_enabled",
        "ads_fovsize",
      ],
      Bezier: [
        "bezier_segments",
        "bezier_ctrl_x",
        "bezier_ctrl_y",
        "bezier_speed",
        "bezier_delay",
        "fovsize",
        "ads_fov_enabled",
        "ads_fovsize",
      ],
    },
  },
  "sec-aimbot": {
    modeKey: "mode_sec",
    fieldsByMode: {
      Normal: [
        "normal_x_speed_sec",
        "normal_y_speed_sec",
        "normalsmooth_sec",
        "fovsize_sec",
        "normalsmoothfov_sec",
        "ads_fov_enabled_sec",
        "ads_fovsize_sec",
      ],
      Silent: [
        "normal_x_speed_sec",
        "normal_y_speed_sec",
        "fovsize_sec",
        "ads_fov_enabled_sec",
        "ads_fovsize_sec",
      ],
      NCAF: [
        "ncaf_alpha_sec",
        "ncaf_snap_boost_sec",
        "ncaf_max_step_sec",
        "ncaf_min_speed_multiplier_sec",
        "ncaf_max_speed_multiplier_sec",
        "ncaf_prediction_interval_sec",
        "ncaf_snap_radius_sec",
        "ncaf_near_radius_sec",
        "ads_fov_enabled_sec",
        "ads_fovsize_sec",
      ],
      WindMouse: [
        "wm_gravity_sec",
        "wm_wind_sec",
        "wm_max_step_sec",
        "wm_min_step_sec",
        "wm_min_delay_sec",
        "wm_max_delay_sec",
        "wm_distance_threshold_sec",
        "fovsize_sec",
        "ads_fov_enabled_sec",
        "ads_fovsize_sec",
      ],
      Bezier: [
        "bezier_segments_sec",
        "bezier_ctrl_x_sec",
        "bezier_ctrl_y_sec",
        "bezier_speed_sec",
        "bezier_delay_sec",
        "fovsize_sec",
        "ads_fov_enabled_sec",
        "ads_fovsize_sec",
      ],
    },
  },
};

function getEl(id) {
  return document.getElementById(id);
}

function setFieldRowVisibility(fieldKey, visible) {
  const input = getEl(fieldKey);
  if (!input) return;
  const row = input.closest(".row");
  if (!row) return;
  row.style.display = visible ? "" : "none";
}

function updateAimbotModeVisibility(section) {
  const modeConfig = AIMBOT_MODE_FIELDS[section];
  if (!modeConfig) return;

  const modeEl = getEl(modeConfig.modeKey);
  const selectedMode = modeEl && modeEl.value ? String(modeEl.value) : "Normal";
  const fieldList = modeConfig.fieldsByMode[selectedMode] || modeConfig.fieldsByMode.Normal;
  const visibleFields = new Set(fieldList);
  const allModeFields = new Set(Object.values(modeConfig.fieldsByMode).flat());

  for (const fieldKey of allModeFields) {
    setFieldRowVisibility(fieldKey, visibleFields.has(fieldKey));
  }
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

function titleFromKey(key) {
  return String(key)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (m) => m.toUpperCase());
}

function parseRangeValue(rawValue, isFloat) {
  const value = isFloat ? parseFloat(rawValue) : parseInt(rawValue, 10);
  if (!Number.isFinite(value)) return null;
  return value;
}

function ensureAllOptionsTab() {
  const nav = document.querySelector(".nav");
  const panel = document.querySelector(".panel");
  if (!nav || !panel) return;

  if (!document.querySelector('.nav-item[data-tab="all-options"]')) {
    const btn = document.createElement("button");
    btn.className = "nav-item";
    btn.dataset.tab = "all-options";
    btn.textContent = "All Options";
    const cfgBtn = document.querySelector('.nav-item[data-tab="config"]');
    if (cfgBtn) nav.insertBefore(btn, cfgBtn);
    else nav.appendChild(btn);
  }

  if (!getEl("tab-all-options")) {
    const tab = document.createElement("div");
    tab.id = "tab-all-options";
    tab.className = "tab-content";
    const wrap = document.createElement("div");
    wrap.id = "all_options_container";
    tab.appendChild(wrap);
    const cfgTab = getEl("tab-config");
    if (cfgTab) panel.insertBefore(tab, cfgTab);
    else panel.appendChild(tab);
  }
  allOptionsContainer = document.getElementById("all_options_container");
}

function appendSelectOptions(selectEl, key) {
  const options = SELECT_OPTIONS[key] || [];
  for (const item of options) {
    const opt = document.createElement("option");
    if (Array.isArray(item)) {
      opt.value = String(item[0]);
      opt.textContent = String(item[1]);
    } else {
      opt.value = String(item);
      opt.textContent = String(item);
    }
    selectEl.appendChild(opt);
  }
}

function createMissingFieldControl(key, type) {
  const row = document.createElement("label");
  row.className = type.startsWith("range-num") ? "row slider-row" : "row";

  const label = document.createElement("span");
  label.textContent = titleFromKey(key);
  row.appendChild(label);

  if (type === "checkbox") {
    const input = document.createElement("input");
    input.id = key;
    input.type = "checkbox";
    row.appendChild(input);
    return row;
  }

  if (type === "select") {
    const select = document.createElement("select");
    select.id = key;
    appendSelectOptions(select, key);
    row.appendChild(select);
    return row;
  }

  if (type.startsWith("range-num")) {
    const meta = RANGE_META[key] || {
      min: type.endsWith("float") ? 0 : 0,
      max: type.endsWith("float") ? 100 : 1000,
      step: type.endsWith("float") ? 0.01 : 1,
    };
    const slider = document.createElement("input");
    slider.id = key;
    slider.type = "range";
    slider.min = String(meta.min);
    slider.max = String(meta.max);
    slider.step = String(meta.step);

    const num = document.createElement("input");
    num.id = `${key}_num`;
    num.className = "num";
    num.type = "number";
    num.min = String(meta.min);
    num.max = String(meta.max);
    num.step = String(meta.step);

    row.appendChild(slider);
    row.appendChild(num);
    return row;
  }

  const input = document.createElement("input");
  input.id = key;
  input.type = "text";
  row.appendChild(input);
  return row;
}

function ensureDynamicFields() {
  ensureAllOptionsTab();
  for (const section of Object.keys(FIELD_MAP)) {
    if (section === "config" || section === "all-options") continue;
    const tab = getEl(`tab-${section}`);
    if (!tab) continue;
    let grid = tab.querySelector(".form-grid");
    if (!grid) {
      grid = document.createElement("div");
      grid.className = "form-grid";
      tab.appendChild(grid);
    }
    for (const [key, type] of FIELD_MAP[section]) {
      if (getEl(key)) continue;
      grid.appendChild(createMissingFieldControl(key, type));
    }
  }
}

function switchTab(tabId) {
  currentTab = tabId;
  navItems.forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === tabId));
  document.querySelectorAll(".tab-content").forEach((el) => el.classList.remove("active"));
  getEl(`tab-${tabId}`).classList.add("active");
  panelTitle.textContent = SECTION_META[tabId].title;
  if (tabId === "all-options" && latestState["all-options"]) {
    renderAllOptions(latestState["all-options"]);
  }
}

function applyStateToSection(section, data) {
  latestState[section] = data;

  if (section === "all-options") {
    if (currentTab === "all-options") {
      renderAllOptions(data);
    }
    if (data.connected && typeof data.connected.overall === "boolean") {
      setConnected(!!data.connected.overall);
    }
    return;
  }

  suppressChange = true;
  for (const [key, type] of FIELD_MAP[section]) {
    const el = getEl(key);
    if (!el || !(key in data)) continue;
    const value = data[key];
    if (type === "checkbox") {
      el.checked = !!value;
    } else if (type === "select" || type === "text") {
      el.value = String(value);
    } else if (type.startsWith("range-num")) {
      const numEl = getEl(`${key}_num`);
      const active = document.activeElement;
      if (active !== el) el.value = String(value);
      if (numEl && active !== numEl) numEl.value = String(value);
    }
  }
  if (data.connected && typeof data.connected.overall === "boolean") {
    setConnected(!!data.connected.overall);
  }
  suppressChange = false;
  if (section === "main-aimbot" || section === "sec-aimbot") {
    updateAimbotModeVisibility(section);
  }
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
        if (
          (section === "main-aimbot" && key === "mode") ||
          (section === "sec-aimbot" && key === "mode_sec")
        ) {
          updateAimbotModeVisibility(section);
        }
        patchSection(section, { [key]: el.value });
      });
    } else if (type === "text") {
      el.addEventListener("change", () => {
        if (suppressChange) return;
        patchSection(section, { [key]: el.value });
      });
    } else if (type.startsWith("range-num")) {
      const isFloat = type.endsWith("float");
      const numEl = getEl(`${key}_num`);
      el.addEventListener("input", () => {
        if (numEl && document.activeElement !== numEl) numEl.value = el.value;
        if (suppressChange) return;
        const value = parseRangeValue(el.value, isFloat);
        if (value === null) return;
        debouncePatch(section, { [key]: value }, 200);
      });
      if (numEl) {
        numEl.addEventListener("input", () => {
          if (suppressChange) return;
          const value = parseRangeValue(numEl.value, isFloat);
          if (value === null) return;
          el.value = String(value);
          debouncePatch(section, { [key]: value }, 200);
        });
        numEl.addEventListener("change", () => {
          const value = parseRangeValue(numEl.value, isFloat);
          if (value === null) return;
          el.value = String(value);
          if (suppressChange) return;
          patchSection(section, { [key]: value });
        });
      }
    }
  }
}

function fullOptionValueType(value) {
  if (Array.isArray(value)) return "json";
  if (value !== null && typeof value === "object") return "json";
  if (typeof value === "boolean") return "bool";
  if (typeof value === "number") return Number.isInteger(value) ? "int" : "float";
  return "string";
}

function fullOptionParseValue(editor, rawValue) {
  const type = editor.dataset.valueType;
  if (type === "bool") return !!editor.checked;
  if (type === "int") {
    const n = parseInt(rawValue, 10);
    return Number.isNaN(n) ? 0 : n;
  }
  if (type === "float") {
    const n = parseFloat(rawValue);
    return Number.isNaN(n) ? 0 : n;
  }
  if (type === "json") {
    try {
      return JSON.parse(rawValue);
    } catch {
      return null;
    }
  }
  return String(rawValue);
}

function createFullOptionRow(key, value) {
  const row = document.createElement("label");
  row.className = "row";

  const span = document.createElement("span");
  span.textContent = key;
  row.appendChild(span);

  const type = fullOptionValueType(value);
  let editor;

  if (type === "bool") {
    editor = document.createElement("input");
    editor.type = "checkbox";
    editor.checked = !!value;
    editor.addEventListener("change", () => {
      patchSection("all-options", { [key]: !!editor.checked });
    });
  } else if (type === "json") {
    editor = document.createElement("textarea");
    editor.className = "num";
    editor.rows = 3;
    editor.value = JSON.stringify(value, null, 2);
    editor.addEventListener("change", () => {
      const parsed = fullOptionParseValue(editor, editor.value);
      if (parsed !== null) patchSection("all-options", { [key]: parsed });
    });
  } else {
    editor = document.createElement("input");
    editor.type = type === "string" ? "text" : "number";
    if (type === "float") editor.step = "0.0001";
    if (type === "int") editor.step = "1";
    editor.value = String(value ?? "");
    editor.addEventListener("change", () => {
      const parsed = fullOptionParseValue(editor, editor.value);
      patchSection("all-options", { [key]: parsed });
    });
  }

  editor.id = `full_${key}`;
  editor.dataset.valueType = type;
  fullOptionEditors.set(key, editor);
  row.appendChild(editor);
  return row;
}

function renderAllOptions(data) {
  if (!allOptionsContainer) return;
  const keys = Object.keys(data)
    .filter((k) => k !== "connected" && k !== "version")
    .sort();

  const stamp = keys.join("|");
  if (allOptionsContainer.dataset.keyStamp !== stamp) {
    allOptionsContainer.innerHTML = "";
    fullOptionEditors.clear();
    const grid = document.createElement("div");
    grid.className = "form-grid";
    for (const key of keys) {
      grid.appendChild(createFullOptionRow(key, data[key]));
    }
    allOptionsContainer.appendChild(grid);
    allOptionsContainer.dataset.keyStamp = stamp;
    return;
  }

  for (const key of keys) {
    const editor = fullOptionEditors.get(key);
    if (!editor) continue;
    if (document.activeElement === editor) continue;
    const type = editor.dataset.valueType;
    const value = data[key];
    if (type === "bool") {
      editor.checked = !!value;
    } else if (type === "json") {
      editor.value = JSON.stringify(value, null, 2);
    } else {
      editor.value = String(value ?? "");
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

  ensureDynamicFields();
  updateAimbotModeVisibility("main-aimbot");
  updateAimbotModeVisibility("sec-aimbot");
  navItems = [...document.querySelectorAll(".nav-item")];
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
