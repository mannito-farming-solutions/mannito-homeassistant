/*
 * Mannito card: one grow area of a Mannito board - climate against its targets, the dryback of the irrigation, the tank,
 * the devices with manual operation and every setting the API token may change.
 *
 *   type: custom:mannito-card
 *   device: <device id of the grow area>
 *   show_all_devices: false   # also the outputs of the board that are not assigned to the area
 *
 * Served and loaded by the Mannito integration; it reads the entities of the area with the websocket command
 * mannito/area and changes them through the normal actions of Home Assistant.
 */

const CARD_VERSION = "0.3.0";

const TEXTS = {
  de: {
    choose: "Grow-Bereich in den Karteneinstellungen wählen.",
    formDevice: "Grow-Bereich",
    formShowAll: "Auch Ausgänge der Platine, die dem Bereich nicht zugeordnet sind",
    loading: "Lädt …",
    overview: "Übersicht",
    devices: "Geräte",
    settings: "Einstellungen",
    climate: "Klima",
    irrigation: "Bewässerung",
    tank: "Tank",
    temperature: "Temperatur",
    humidity: "Luftfeuchte",
    vpd: "VPD",
    co2: "CO₂",
    leaf: "Blatt",
    intake: "Zuluft",
    target: "Soll",
    day: "Tag",
    night: "Nacht",
    dayOfGrow: "Tag",
    phaseDay: "Phasentag",
    substrate: "Substrat",
    peak: "Tageshoch",
    fieldCapacity: "Feldkapazität",
    trigger: "P2-Auslöser",
    emergencyLine: "Notfall",
    emergencyMode: "Notbetrieb: Die Platine regelt mit voller Leistung gegen.",
    shots: "Shots heute",
    water: "ml / Topf heute",
    dryback: "Dryback",
    nextShot: "Nächster Shot",
    lastShot: "Letzter Shot",
    inMin: "in {n} min",
    ago: "vor {t}",
    runValves: "Ventile {n} s",
    runValvesConfirm: "Alle Ventile dieses Bereichs nacheinander je {n} Sekunden öffnen?",
    manual: "Hand",
    automatic: "Automatik",
    on: "an",
    off: "aus",
    open: "{n} s öffnen",
    close: "Schließen",
    opened: "offen",
    closed: "zu",
    notAssigned: "Weitere Ausgänge der Platine",
    noDevices: "Keine Geräte freigegeben (Token ohne Recht „Steuern“).",
    control: "Regelung",
    climateControl: "Klimaregelung",
    irrigationMode: "Bewässerung",
    strategy: "Dryback-Steuerung",
    drybackValues: "Dryback-Werte",
    customHint: "Ein geänderter Wert stellt die Steuerung auf „Eigene Werte“.",
    growCycle: "Grow-Zyklus",
    lightsOn: "Licht an",
    set: "Setzen",
    nextPhase: "Nächste Phase starten",
    nextPhaseConfirm: "Die nächste Phase jetzt starten? Die Zeitpläne des Bereichs wechseln sofort.",
    confirmPhase: "Phase bestätigen",
    confirmPhaseConfirm: "Die laufende Phase (Ernte oder Trocknung) als erledigt bestätigen?",
    postpone: "Verschieben",
    days: "Tage",
    firmware: "Firmware",
    install: "Installieren",
    installConfirm: "Firmware {v} installieren? Die Platine startet neu und regelt einige Minuten nicht.",
    upToDate: "aktuell",
    noConfigure: "Einstellungen brauchen einen Token mit dem Recht „Konfigurieren“.",
    status: { ok: "In Ordnung", attention: "Achtung", problem: "Problem", neutral: "Pausiert", nodata: "Keine Werte" },
    plants: "Pflanzen",
    age: "Tag {n}",
    height: "Höhe",
    measuredAgo: "gemessen {t}",
    notMeasured: "noch nicht gemessen",
    heightCm: "Höhe cm",
    save: "Speichern",
    note: "Beobachtung …",
    problemToggle: "Problem",
    conditions: { perfect: "Perfekt", acceptable: "In Ordnung", warning: "Warnung", total_fail: "Ausfall" },
    saved: "Gespeichert.",
    openProblems: "{n} offene Probleme",
    openProblem: "1 offenes Problem",
    noPlants: "In diesem Bereich stehen keine Pflanzen.",
    liters: "Liter",
    topUp: "Nachgefüllt",
    fresh: "Frisch angemischt",
    levelCheck: "Füllstand",
    tankConfirm: "{kind}: {l} l eintragen?",
    targets: "Sollwerte der Phase",
    targetsHint: "Gilt für die laufende Phase; die Zeitpläne folgen sofort.",
    fieldCapacityNow: "Feldkapazität jetzt messen",
    fieldCapacityConfirm: "Den aktuellen Wert der Sonde als Feldkapazität speichern? (Topf durchnässt und 30-60 min abgetropft)",
    p1: "P1 · Auffüllen",
    p2: "P2 · Halten",
    p3: "P3 · Nacht",
    p0: "P0 · Morgen",
    numbers: {
      p1_start: "P1-Start nach Licht an",
      p1_shot: "P1-Shot",
      p1_interval: "P1-Abstand",
      p1_max_shots: "P1 max. Shots",
      p1_target: "P1-Ziel",
      p2_shot: "P2-Shot",
      p2_dryback: "P2-Auslöser unter Hoch",
      p2_min_interval: "P2-Mindestabstand",
      p2_end: "P2-Ende vor Licht aus",
      min_vwc: "Notfall-Feuchte",
      fallback_interval: "Abstand ohne Sonde",
      max_day_shots: "Shots / Tag max.",
      max_day_ml: "ml / Topf und Tag max.",
      day_temperature: "Tag-Temperatur",
      night_temperature: "Nacht-Temperatur",
      day_vpd: "VPD Tag",
      night_vpd: "VPD Nacht",
      day_humidity: "Luftfeuchte Tag",
      night_humidity: "Luftfeuchte Nacht",
      light_intensity: "Lichtstärke",
      co2_day: "CO₂ bei Licht",
      circulation: "Umluft",
    },
  },
  en: {
    choose: "Choose a grow area in the card settings.",
    formDevice: "Grow area",
    formShowAll: "Also show board outputs not assigned to this area",
    loading: "Loading …",
    overview: "Overview",
    devices: "Devices",
    settings: "Settings",
    climate: "Climate",
    irrigation: "Irrigation",
    tank: "Tank",
    temperature: "Temperature",
    humidity: "Humidity",
    vpd: "VPD",
    co2: "CO₂",
    leaf: "Leaf",
    intake: "Intake",
    target: "Target",
    day: "Day",
    night: "Night",
    dayOfGrow: "Day",
    phaseDay: "Phase day",
    substrate: "Substrate",
    peak: "Peak",
    fieldCapacity: "Field capacity",
    trigger: "P2 trigger",
    emergencyLine: "Emergency",
    emergencyMode: "Emergency mode: the board is correcting at full power.",
    shots: "Shots today",
    water: "ml / pot today",
    dryback: "Dryback",
    nextShot: "Next shot",
    lastShot: "Last shot",
    inMin: "in {n} min",
    ago: "{t} ago",
    runValves: "Valves {n} s",
    runValvesConfirm: "Open every valve of this area for {n} seconds, one after another?",
    manual: "Manual",
    automatic: "Automatic",
    on: "on",
    off: "off",
    open: "Open {n} s",
    close: "Close",
    opened: "open",
    closed: "closed",
    notAssigned: "Other outputs of the board",
    noDevices: "No devices. The API token has no Control right.",
    control: "Control",
    climateControl: "Climate control",
    irrigationMode: "Irrigation",
    strategy: "Dryback strategy",
    drybackValues: "Dryback values",
    customHint: "Changing a value switches the strategy to Custom.",
    growCycle: "Grow cycle",
    lightsOn: "Lights on",
    set: "Set",
    nextPhase: "Start next phase",
    nextPhaseConfirm: "Start the next phase now? The schedules of this area change right away.",
    confirmPhase: "Confirm phase",
    confirmPhaseConfirm: "Mark the current phase (harvest or drying) as done?",
    postpone: "Postpone",
    days: "days",
    firmware: "Firmware",
    install: "Install",
    installConfirm: "Install firmware {v}? The board restarts and stops regulating for a few minutes.",
    upToDate: "up to date",
    noConfigure: "Changing settings needs an API token with the Configure right.",
    status: { ok: "OK", attention: "Attention", problem: "Problem", neutral: "Paused", nodata: "No data" },
    plants: "Plants",
    age: "Day {n}",
    height: "Height",
    measuredAgo: "measured {t}",
    notMeasured: "not measured yet",
    heightCm: "Height cm",
    save: "Save",
    note: "Observation …",
    problemToggle: "Problem",
    conditions: { perfect: "Perfect", acceptable: "Fine", warning: "Warning", total_fail: "Lost" },
    saved: "Saved.",
    openProblems: "{n} open problems",
    openProblem: "1 open problem",
    noPlants: "No plants in this area.",
    liters: "Liters",
    topUp: "Topped up",
    fresh: "Mixed fresh",
    levelCheck: "Level",
    tankConfirm: "Log {kind}: {l} l?",
    targets: "Phase targets",
    targetsHint: "Applies to the current phase. The schedules update right away.",
    fieldCapacityNow: "Measure field capacity now",
    fieldCapacityConfirm: "Save the current probe reading as field capacity? Do this once the pot is soaked and has drained for 30-60 min.",
    p1: "P1 · Ramp",
    p2: "P2 · Maintain",
    p3: "P3 · Night",
    p0: "P0 · Morning",
    numbers: {
      p1_start: "P1 start after lights on",
      p1_shot: "P1 shot",
      p1_interval: "P1 interval",
      p1_max_shots: "P1 max shots",
      p1_target: "P1 target",
      p2_shot: "P2 shot",
      p2_dryback: "P2 trigger below peak",
      p2_min_interval: "P2 min interval",
      p2_end: "P2 end before lights off",
      min_vwc: "Emergency moisture",
      fallback_interval: "Interval without probe",
      max_day_shots: "Shots / day max",
      max_day_ml: "ml / pot and day max",
      day_temperature: "Day temperature",
      night_temperature: "Night temperature",
      day_vpd: "Day VPD",
      night_vpd: "Night VPD",
      day_humidity: "Day humidity",
      night_humidity: "Night humidity",
      light_intensity: "Light intensity",
      co2_day: "CO₂ with lights on",
      circulation: "Circulation",
    },
  },
};

const PHASE_KEYS = ["day_temperature", "night_temperature", "day_vpd", "night_vpd", "day_humidity", "night_humidity", "light_intensity", "co2_day", "circulation"];

const NUMBER_KEYS = [
  "p1_start", "p1_shot", "p1_interval", "p1_max_shots", "p1_target", "p2_shot", "p2_dryback",
  "p2_min_interval", "p2_end", "min_vwc", "fallback_interval", "max_day_shots", "max_day_ml",
];

// climate tiles: entity key, target key, tolerance for the colour of the deviation
const CLIMATE = [
  { key: "temperature", target: "target_temperature", label: "temperature", icon: "mdi:thermometer", tolerance: 1.0 },
  { key: "humidity", target: "target_humidity", label: "humidity", icon: "mdi:water-percent", tolerance: 5 },
  { key: "vpd", target: "target_vpd", label: "vpd", icon: "mdi:leaf", tolerance: 0.15 },
  { key: "co2", target: "target_co2", label: "co2", icon: "mdi:molecule-co2", tolerance: 150 },
  { key: "leaf_temperature", label: "leaf", icon: "mdi:leaf-maple" },
  { key: "intake_temperature", second: "intake_humidity", label: "intake", icon: "mdi:air-filter" },
];

const TYPE_ICONS = {
  light: "mdi:lightbulb", dimmer: "mdi:brightness-6", fan: "mdi:fan", valve: "mdi:valve", socket: "mdi:power-socket-eu",
  relay: "mdi:electric-switch", heater: "mdi:radiator", cooler: "mdi:snowflake", water_pump: "mdi:pump", dosing_pump: "mdi:eyedropper",
};

const VALVE_SECONDS = 10;

const BAD = new Set(["unavailable", "unknown", undefined, null, ""]);

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

class MannitoCard extends HTMLElement {
  static getConfigForm() {
    return {
      schema: [
        { name: "device", required: true, selector: { device: { filter: { integration: "mannito" } } } },
        { name: "show_all_devices", selector: { boolean: {} } },
      ],
      computeLabel: (schema) => {
        const t = MannitoCard.texts(document.querySelector("home-assistant")?.hass);
        return { device: t.formDevice, show_all_devices: t.formShowAll }[schema.name];
      },
    };
  }

  static getStubConfig() {
    return { device: "" };
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._tab = "overview";
    this._info = null;
    this._error = null;
    this._loadingFor = null;
    this._built = false;
  }

  setConfig(config) {
    if (!config) throw new Error("Invalid configuration");
    const changed = !this._config || this._config.device !== config.device || this._config.show_all_devices !== config.show_all_devices;
    this._config = { show_all_devices: false, ...config };
    if (changed) {
      this._info = null;
      this._error = null;
      this._built = false;
      this._render();
    }
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config?.device) {
      this._render();
      return;
    }
    if (!this._info && this._loadingFor !== this._config.device) {
      this._load();
      return;
    }
    if (this._built) this._update();
  }

  getCardSize() {
    return 9;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6, rows: "auto" };
  }

  static texts(hass) {
    const lang = (hass?.locale?.language || hass?.language || "en").slice(0, 2);
    return TEXTS[lang] || TEXTS.en;
  }

  get _t() {
    return MannitoCard.texts(this._hass);
  }

  async _load() {
    const device = this._config.device;
    this._loadingFor = device;
    try {
      const info = await this._hass.callWS({ type: "mannito/area", device_id: device });
      if (this._config.device !== device) return;
      this._info = info;
      this._error = null;
      this._loadTimeline();
    } catch (err) {
      this._error = err?.message || String(err);
    } finally {
      this._loadingFor = null;
    }
    this._built = false;
    this._render();
  }

  async _loadTimeline() {
    const calendar = this._info?.entities?.grow_phases;
    if (!calendar || !this._hass.callApi) return;
    const start = new Date(Date.now() - 365 * 86400000).toISOString();
    const end = new Date(Date.now() + 365 * 86400000).toISOString();
    try {
      const events = await this._hass.callApi("GET", `calendars/${calendar}?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`);
      this._timeline = (events || []).map((e) => ({
        name: e.summary,
        start: new Date(e.start.dateTime || e.start.date),
        end: new Date(e.end.dateTime || e.end.date),
      }));
    } catch (_err) {
      this._timeline = [];
    }
    if (this._built) this._renderTimeline();
  }

  _renderTimeline() {
    const el = this.shadowRoot.querySelector('[data-bind="timeline"]');
    const spans = (this._timeline || []).filter((s) => s.end > s.start);
    if (!el) return;
    if (!spans.length) {
      el.hidden = true;
      return;
    }
    const first = Math.min(...spans.map((s) => s.start.getTime()));
    const last = Math.max(...spans.map((s) => s.end.getTime()));
    const now = Date.now();
    const pct = (ms) => Math.max(0, Math.min(100, ((ms - first) / (last - first)) * 100));
    const fmt = new Intl.DateTimeFormat(this._hass?.locale?.language || this._hass?.language || "en", { day: "2-digit", month: "2-digit" });
    el.hidden = false;
    el.innerHTML = `<div class="tl-bar">${spans
      .map((s) => {
        const state = s.end.getTime() <= now ? "done" : s.start.getTime() <= now ? "current" : "planned";
        return `<div class="tl-seg ${state}" style="left:${pct(s.start.getTime())}%;width:${pct(s.end.getTime()) - pct(s.start.getTime())}%"
                  title="${esc(s.name)} · ${fmt.format(s.start)} - ${fmt.format(s.end)}"><span>${esc(s.name)}</span></div>`;
      })
      .join("")}<div class="tl-now" style="left:${pct(now)}%"></div></div>`;
  }

  // ---------------------------------------------------------------------------------------------------------- helpers

  _entity(key) {
    const id = this._info?.entities?.[key];
    return id ? this._hass.states[id] : undefined;
  }

  _num(key) {
    const state = this._entity(key)?.state;
    if (BAD.has(state)) return null;
    const value = Number(state);
    return Number.isFinite(value) ? value : null;
  }

  _fmt(stateObj, fallback = "–") {
    if (!stateObj || BAD.has(stateObj.state)) return fallback;
    try {
      return this._hass.formatEntityState ? this._hass.formatEntityState(stateObj) : `${stateObj.state} ${stateObj.attributes.unit_of_measurement || ""}`;
    } catch (_err) {
      return stateObj.state;
    }
  }

  _fmtNumber(value, digits) {
    if (value === null || value === undefined) return "–";
    return new Intl.NumberFormat(this._hass?.locale?.language || this._hass?.language || "en", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value);
  }

  _text(template, values) {
    return template.replace(/\{(\w+)\}/g, (_m, key) => values[key] ?? "");
  }

  _moreInfo(entityId) {
    if (!entityId) return;
    this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
  }

  _toast(message) {
    this.dispatchEvent(new CustomEvent("hass-notification", { detail: { message }, bubbles: true, composed: true }));
  }

  async _call(domain, service, data, target) {
    try {
      await this._hass.callService(domain, service, data, target);
    } catch (err) {
      this._toast(err?.message || String(err));
    }
  }

  _relative(iso) {
    if (!iso || BAD.has(iso)) return null;
    const seconds = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
    if (!Number.isFinite(seconds)) return null;
    const rtf = new Intl.RelativeTimeFormat(this._hass?.locale?.language || this._hass?.language || "en", { numeric: "auto", style: "short" });
    if (Math.abs(seconds) < 3600) return rtf.format(-Math.round(seconds / 60), "minute");
    if (Math.abs(seconds) < 86400) return rtf.format(-Math.round(seconds / 3600), "hour");
    return rtf.format(-Math.round(seconds / 86400), "day");
  }

  // ---------------------------------------------------------------------------------------------------------- render

  _render() {
    const t = this._t;
    if (!this._config?.device) {
      this.shadowRoot.innerHTML = `${STYLE}<ha-card><div class="empty"><ha-icon icon="mdi:sprout"></ha-icon><span>${esc(t.choose)}</span></div></ha-card>`;
      return;
    }
    if (this._error) {
      this.shadowRoot.innerHTML = `${STYLE}<ha-card><div class="empty error"><ha-icon icon="mdi:alert-circle-outline"></ha-icon><span>${esc(this._error)}</span></div></ha-card>`;
      return;
    }
    if (!this._info || !this._hass) {
      this.shadowRoot.innerHTML = `${STYLE}<ha-card><div class="empty"><ha-icon icon="mdi:loading"></ha-icon><span>${esc(t.loading)}</span></div></ha-card>`;
      return;
    }
    this.shadowRoot.innerHTML = `${STYLE}<ha-card>${this._skeleton()}</ha-card>`;
    this._built = true;
    this._bind();
    this._update();
    this._renderTimeline();
  }

  _skeleton() {
    const t = this._t;
    const info = this._info;
    const tabs = [["overview", t.overview, "mdi:view-dashboard-outline"], ["devices", t.devices, "mdi:tune-vertical"]];
    if ((info.plants || []).length) tabs.splice(1, 0, ["plants", t.plants, "mdi:sprout-outline"]);
    if (info.can_configure) tabs.push(["settings", t.settings, "mdi:cog-outline"]);
    return `
      <div class="header">
        <div class="title-row">
          <ha-icon class="title-icon" icon="mdi:sprout"></ha-icon>
          <div class="title">
            <div class="name">${esc(info.name)}</div>
            <div class="sub" data-bind="sub"></div>
          </div>
          <div class="chip" data-bind="status"></div>
        </div>
        <div class="banner" data-bind="emergency" hidden></div>
        <div class="light-row" data-bind="light"></div>
      </div>
      <div class="tabs">
        ${tabs.map(([id, label, icon]) => `<button class="tab ${this._tab === id ? "active" : ""}" data-tab="${id}"><ha-icon icon="${icon}"></ha-icon><span>${esc(label)}</span></button>`).join("")}
      </div>
      <div class="pane" data-pane="overview" ${this._tab === "overview" ? "" : "hidden"}>${this._overviewSkeleton()}</div>
      ${(info.plants || []).length ? `<div class="pane" data-pane="plants" ${this._tab === "plants" ? "" : "hidden"}>${this._plantsSkeleton()}</div>` : ""}
      <div class="pane" data-pane="devices" ${this._tab === "devices" ? "" : "hidden"}>${this._devicesSkeleton()}</div>
      ${info.can_configure ? `<div class="pane" data-pane="settings" ${this._tab === "settings" ? "" : "hidden"}>${this._settingsSkeleton()}</div>` : ""}
    `;
  }

  _overviewSkeleton() {
    const t = this._t;
    const tiles = CLIMATE.filter((c) => this._info.entities[c.key]).map(
      (c) => `
      <button class="tile" data-more="${c.key}">
        <div class="tile-head"><ha-icon icon="${c.icon}"></ha-icon><span>${esc(t[c.label])}</span></div>
        <div class="tile-value" data-bind="v-${c.key}">–</div>
        ${c.target ? `<div class="tile-target" data-bind="t-${c.key}"></div><div class="dev"><div class="dev-mid"></div><div class="dev-dot" data-bind="d-${c.key}"></div></div>` : `<div class="tile-target" data-bind="s-${c.key}"></div>`}
      </button>`,
    );
    const hasIrrigation = Boolean(this._info.entities.substrate_moisture);
    const hasTank = Boolean(this._info.entities.tank_volume);
    return `
      <div class="timeline" data-bind="timeline" hidden></div>
      <div class="section-title">${esc(t.climate)}</div>
      <div class="tiles">${tiles.join("")}</div>
      ${hasIrrigation ? `
      <div class="section-title row-between"><span>${esc(t.irrigation)}</span><span class="phase-chip" data-bind="irr-phase"></span></div>
      <div class="moisture" data-more-id="substrate_moisture">
        <div class="moisture-head"><span>${esc(t.substrate)}</span><span class="big" data-bind="vwc">–</span></div>
        <div class="scale" data-bind="scale">
          <div class="fill" data-bind="vwc-fill"></div>
          <div class="mark peak" data-bind="m-peak" title="${esc(t.peak)}"></div>
          <div class="mark fc" data-bind="m-fc" title="${esc(t.fieldCapacity)}"></div>
          <div class="mark trigger" data-bind="m-trigger" title="${esc(t.trigger)}"></div>
          <div class="mark emergency" data-bind="m-min" title="${esc(t.emergencyLine)}"></div>
        </div>
        <div class="legend" data-bind="legend"></div>
      </div>
      <div class="stats">
        <div class="stat"><div class="stat-v" data-bind="shots">–</div><div class="stat-l">${esc(t.shots)}</div></div>
        <div class="stat"><div class="stat-v" data-bind="water">–</div><div class="stat-l">${esc(t.water)}</div></div>
        <div class="stat"><div class="stat-v" data-bind="dryback">–</div><div class="stat-l">${esc(t.dryback)}</div></div>
        <div class="stat"><div class="stat-v" data-bind="next">–</div><div class="stat-l" data-bind="next-l">${esc(t.nextShot)}</div></div>
      </div>` : ""}
      ${hasTank ? `
      <div class="section-title row-between"><span>${esc(t.tank)}</span><span class="muted" data-bind="tank-text"></span></div>
      <div class="bar tank" data-more-id="tank_volume"><div class="bar-fill" data-bind="tank-fill"></div></div>
      ${this._info.can_control ? `
      <div class="inline tank-book">
        <input type="number" min="0" max="1000" step="0.5" value="1" data-tank-liters aria-label="${esc(t.liters)}"><span class="unit">l</span>
        <button class="btn small ghost" data-tank="top_up">${esc(t.topUp)}</button>
        <button class="btn small ghost" data-tank="fresh">${esc(t.fresh)}</button>
        <button class="btn small ghost" data-tank="level_check">${esc(t.levelCheck)}</button>
      </div>` : ""}` : ""}
      ${hasIrrigation && this._info.can_control ? `
      <div class="actions">
        <button class="btn" data-action="run-valves"><ha-icon icon="mdi:sprinkler-variant"></ha-icon>${esc(this._text(t.runValves, { n: VALVE_SECONDS }))}</button>
      </div>` : ""}
    `;
  }

  _plantsSkeleton() {
    const t = this._t;
    const plants = this._info.plants || [];
    if (!plants.length) return `<div class="empty small">${esc(t.noPlants)}</div>`;
    const canRecord = this._info.can_control;
    const conditions = Object.entries(t.conditions).map(([k, v]) => `<option value="${k}" ${k === "acceptable" ? "selected" : ""}>${esc(v)}</option>`).join("");
    return `
      <div class="muted small hint" data-bind="problems"></div>
      <div class="plants">${plants
        .map(
          (p) => `
        <div class="plant" data-plant="${p.plant_id}">
          <div class="plant-head">
            <ha-icon icon="mdi:cannabis"></ha-icon>
            <div class="plant-title"><div class="plant-name">${esc(p.name)}</div><div class="muted small">${esc(p.variety || "")}${p.days != null ? ` · ${esc(this._text(t.age, { n: p.days }))}` : ""}</div></div>
            <button class="plant-height" data-plant-more="${p.plant_id}"><span class="big" data-bind="ph-${p.plant_id}">–</span><span class="muted small" data-bind="pm-${p.plant_id}"></span></button>
          </div>
          ${canRecord && p.device_id ? `
          <div class="inline plant-actions">
            <input type="number" min="0" max="1000" step="0.5" placeholder="${esc(t.heightCm)}" data-height="${p.plant_id}" aria-label="${esc(t.heightCm)}">
            <button class="btn small" data-save-height="${p.plant_id}"><ha-icon icon="mdi:ruler"></ha-icon>${esc(t.save)}</button>
          </div>
          <input type="text" maxlength="1000" placeholder="${esc(t.note)}" data-note="${p.plant_id}" class="note-input" aria-label="${esc(t.note)}">
          <div class="inline plant-actions">
            <select data-condition="${p.plant_id}" aria-label="${esc(t.note)}">${conditions}</select>
            <label class="check"><input type="checkbox" data-problem="${p.plant_id}">${esc(t.problemToggle)}</label>
            <button class="btn small ghost push" data-save-note="${p.plant_id}"><ha-icon icon="mdi:note-edit-outline"></ha-icon>${esc(t.save)}</button>
          </div>` : ""}
        </div>`,
        )
        .join("")}</div>`;
  }

  _visibleOutputs() {
    const outputs = this._info.outputs || [];
    const assigned = outputs.filter((o) => o.assigned);
    if (this._config.show_all_devices || assigned.length === 0) return { main: assigned.length ? assigned : outputs, rest: assigned.length ? outputs.filter((o) => !o.assigned) : [] };
    return { main: assigned, rest: [] };
  }

  _outputRow(o) {
    const t = this._t;
    const control = o.entities.control;
    let widget = "";
    if (control && o.type === "valve") {
      widget = `<button class="btn small" data-valve="${o.device_id}">${esc(this._text(t.open, { n: VALVE_SECONDS }))}</button>
                <button class="btn small ghost" data-valve-close="${o.device_id}">${esc(t.close)}</button>`;
    } else if (control) {
      widget = `${o.dimmable ? `<input class="slider" type="range" min="1" max="100" step="1" data-level="${o.device_id}">` : ""}
                <label class="toggle"><input type="checkbox" data-toggle="${o.device_id}"><span></span></label>`;
    }
    return `
      <div class="device" data-device="${o.device_id}">
        <button class="dev-icon" data-more-device="${o.device_id}"><ha-icon icon="${TYPE_ICONS[o.type] || "mdi:power"}"></ha-icon></button>
        <div class="dev-name">
          <div>${esc(o.name)}</div>
          <div class="muted small">${o.function_name ? `${esc(o.function_name)} · ` : ""}<span data-bind="state-${o.device_id}"></span></div>
        </div>
        <div class="dev-controls">
          <span class="badge manual" data-bind="manual-${o.device_id}" hidden>${esc(t.manual)}</span>
          ${widget}
          ${o.entities.automatic ? `<button class="icon-btn" title="${esc(t.automatic)}" data-auto="${o.device_id}"><ha-icon icon="mdi:robot-outline"></ha-icon></button>` : ""}
        </div>
      </div>`;
  }

  _devicesSkeleton() {
    const t = this._t;
    const { main, rest } = this._visibleOutputs();
    if (!main.length && !rest.length) return `<div class="empty small">${esc(t.noDevices)}</div>`;
    return `
      <div class="device-list">${main.map((o) => this._outputRow(o)).join("")}</div>
      ${rest.length ? `<div class="section-title">${esc(t.notAssigned)}</div><div class="device-list">${rest.map((o) => this._outputRow(o)).join("")}</div>` : ""}
    `;
  }

  _settingsSkeleton() {
    const t = this._t;
    const e = this._info.entities;
    const select = (key, label) =>
      e[key] ? `<label class="field"><span>${esc(label)}</span><select data-select="${key}"></select></label>` : "";
    const phaseNumbers = PHASE_KEYS.filter((k) => e[k]).map(
      (k) => `<label class="field num"><span>${esc(t.numbers[k])}</span><div class="num-wrap"><input type="number" data-number="${k}"><span class="unit" data-bind="u-${k}"></span></div></label>`,
    );
    const numbers = NUMBER_KEYS.filter((k) => e[k]).map(
      (k) => `<label class="field num"><span>${esc(t.numbers[k])}</span><div class="num-wrap"><input type="number" data-number="${k}"><span class="unit" data-bind="u-${k}"></span></div></label>`,
    );
    const firmware = this._info.board_entities?.firmware;
    return `
      <div class="settings-grid">
        ${e.control ? `<div class="field"><span>${esc(t.control)}</span><label class="toggle"><input type="checkbox" data-area-control><span></span></label></div>` : ""}
        ${select("climate_control", t.climateControl)}
        ${select("irrigation_mode", t.irrigationMode)}
        ${select("dryback_strategy", t.strategy)}
      </div>
      ${phaseNumbers.length || e.lights_on ? `<div class="section-title">${esc(t.targets)}</div><div class="muted small hint">${esc(t.targetsHint)}</div>
      <div class="settings-grid">
        ${e.lights_on ? `<label class="field"><span>${esc(t.lightsOn)}</span><input type="time" data-time="lights_on"></label>` : ""}
        ${phaseNumbers.join("")}
      </div>` : ""}
      ${numbers.length ? `<div class="section-title">${esc(t.drybackValues)}</div><div class="muted small hint">${esc(t.customHint)}</div><div class="settings-grid">${numbers.join("")}</div>` : ""}
      ${e.field_capacity_now ? `<div class="actions"><button class="btn ghost" data-action="field-capacity"><ha-icon icon="mdi:water-check"></ha-icon>${esc(t.fieldCapacityNow)}</button></div>` : ""}
      <div class="section-title">${esc(t.growCycle)}</div>
      <div class="settings-grid">
        ${e.lights_on ? "" : `<label class="field"><span>${esc(t.lightsOn)}</span><div class="inline"><input type="time" data-lights-on><button class="btn small" data-action="lights-on">${esc(t.set)}</button></div></label>`}
        <label class="field"><span>${esc(t.postpone)}</span><div class="inline"><input type="number" min="1" max="14" value="1" data-postpone-days><span class="unit">${esc(t.days)}</span><button class="btn small" data-action="postpone">${esc(t.postpone)}</button></div></label>
      </div>
      <div class="actions">
        <button class="btn ghost" data-action="next-phase"><ha-icon icon="mdi:skip-next"></ha-icon>${esc(t.nextPhase)}</button>
        <button class="btn ghost" data-action="confirm-phase"><ha-icon icon="mdi:check-decagram-outline"></ha-icon>${esc(t.confirmPhase)}</button>
      </div>
      ${firmware ? `
      <div class="section-title">${esc(t.firmware)}</div>
      <div class="row-between"><span data-bind="fw-text"></span><button class="btn small" data-action="firmware" hidden>${esc(t.install)}</button></div>` : ""}
    `;
  }

  // ---------------------------------------------------------------------------------------------------------- events

  _bind() {
    const root = this.shadowRoot;
    const t = this._t;
    const area = { area: this._config.device };
    root.querySelectorAll("[data-tab]").forEach((el) =>
      el.addEventListener("click", () => {
        this._tab = el.dataset.tab;
        root.querySelectorAll("[data-tab]").forEach((b) => b.classList.toggle("active", b.dataset.tab === this._tab));
        root.querySelectorAll("[data-pane]").forEach((p) => (p.hidden = p.dataset.pane !== this._tab));
      }),
    );
    root.querySelectorAll("[data-more]").forEach((el) => el.addEventListener("click", () => this._moreInfo(this._info.entities[el.dataset.more])));
    root.querySelectorAll("[data-more-id]").forEach((el) => el.addEventListener("click", () => this._moreInfo(this._info.entities[el.dataset.moreId])));
    const output = (id) => this._info.outputs.find((o) => o.device_id === id);
    root.querySelectorAll("[data-more-device]").forEach((el) =>
      el.addEventListener("click", () => this._moreInfo(output(el.dataset.moreDevice)?.entities.control || output(el.dataset.moreDevice)?.entities.on)),
    );
    root.querySelectorAll("[data-toggle]").forEach((el) =>
      el.addEventListener("change", () => {
        const o = output(el.dataset.toggle);
        const domain = o.entities.control.split(".")[0];
        this._call(domain, el.checked ? "turn_on" : "turn_off", {}, { entity_id: o.entities.control });
      }),
    );
    root.querySelectorAll("[data-level]").forEach((el) =>
      el.addEventListener("change", () => {
        const o = output(el.dataset.level);
        const domain = o.entities.control.split(".")[0];
        const value = Number(el.value);
        if (domain === "fan") this._call("fan", "set_percentage", { percentage: value }, { entity_id: o.entities.control });
        else this._call("light", "turn_on", { brightness_pct: value }, { entity_id: o.entities.control });
      }),
    );
    root.querySelectorAll("[data-valve]").forEach((el) =>
      el.addEventListener("click", () =>
        this._call("mannito", "open_valve", { duration: VALVE_SECONDS }, { entity_id: output(el.dataset.valve).entities.control }),
      ),
    );
    root.querySelectorAll("[data-valve-close]").forEach((el) =>
      el.addEventListener("click", () => this._call("valve", "close_valve", {}, { entity_id: output(el.dataset.valveClose).entities.control })),
    );
    root.querySelectorAll("[data-auto]").forEach((el) =>
      el.addEventListener("click", () => this._call("button", "press", {}, { entity_id: output(el.dataset.auto).entities.automatic })),
    );
    root.querySelectorAll("[data-select]").forEach((el) =>
      el.addEventListener("change", () => this._call("select", "select_option", { option: el.value }, { entity_id: this._info.entities[el.dataset.select] })),
    );
    root.querySelectorAll("[data-number]").forEach((el) =>
      el.addEventListener("change", () => {
        if (el.value === "") return;
        this._call("number", "set_value", { value: Number(el.value) }, { entity_id: this._info.entities[el.dataset.number] });
      }),
    );
    root.querySelector('[data-time="lights_on"]')?.addEventListener("change", (ev) => {
      if (ev.target.value) this._call("time", "set_value", { time: `${ev.target.value}:00` }, { entity_id: this._info.entities.lights_on });
    });
    root.querySelectorAll("[data-tank]").forEach((el) =>
      el.addEventListener("click", () => {
        const liters = Number(root.querySelector("[data-tank-liters]").value);
        if (!(liters >= 0)) return;
        const label = { top_up: t.topUp, fresh: t.fresh, level_check: t.levelCheck }[el.dataset.tank];
        if (confirm(this._text(t.tankConfirm, { kind: label, l: liters }))) {
          this._call("mannito", "tank_entry", { area: this._config.device, kind: el.dataset.tank, liters });
        }
      }),
    );
    const plant = (id) => (this._info.plants || []).find((p) => p.plant_id === id);
    root.querySelectorAll("[data-plant-more]").forEach((el) =>
      el.addEventListener("click", () => this._moreInfo(plant(el.dataset.plantMore)?.entities.height)),
    );
    root.querySelectorAll("[data-save-height]").forEach((el) =>
      el.addEventListener("click", async () => {
        const input = root.querySelector(`[data-height="${el.dataset.saveHeight}"]`);
        const value = Number(input.value);
        if (!input.value || !(value > 0)) return;
        await this._call("mannito", "record_measurement", { target: plant(el.dataset.saveHeight).device_id, measurement: "height", value });
        input.value = "";
      }),
    );
    root.querySelectorAll("[data-save-note]").forEach((el) =>
      el.addEventListener("click", async () => {
        const id = el.dataset.saveNote;
        const note = root.querySelector(`[data-note="${id}"]`);
        const problem = root.querySelector(`[data-problem="${id}"]`);
        await this._call("mannito", "record_note", {
          target: plant(id).device_id,
          condition: root.querySelector(`[data-condition="${id}"]`).value,
          note: note.value || undefined,
          problem: problem.checked,
        });
        note.value = "";
        problem.checked = false;
      }),
    );
    root.querySelector("[data-area-control]")?.addEventListener("change", (ev) =>
      this._call("switch", ev.target.checked ? "turn_on" : "turn_off", {}, { entity_id: this._info.entities.control }),
    );
    const action = (name, handler) => root.querySelector(`[data-action="${name}"]`)?.addEventListener("click", handler);
    action("run-valves", () => {
      if (confirm(this._text(t.runValvesConfirm, { n: VALVE_SECONDS }))) this._call("mannito", "run_valves", { ...area, seconds: VALVE_SECONDS });
    });
    action("lights-on", (ev) => {
      ev.preventDefault();
      const value = root.querySelector("[data-lights-on]").value;
      if (value) this._call("mannito", "grow_cycle_action", { ...area, action: "set_lights_on", lights_on: value });
    });
    action("postpone", (ev) => {
      ev.preventDefault();
      const days = Number(root.querySelector("[data-postpone-days]").value || 1);
      this._call("mannito", "grow_cycle_action", { ...area, action: "postpone", days });
    });
    action("field-capacity", () => {
      if (confirm(t.fieldCapacityConfirm)) this._call("button", "press", {}, { entity_id: this._info.entities.field_capacity_now });
    });
    action("next-phase", () => {
      if (confirm(t.nextPhaseConfirm)) this._call("mannito", "grow_cycle_action", { ...area, action: "next_phase_now" });
    });
    action("confirm-phase", () => {
      if (confirm(t.confirmPhaseConfirm)) this._call("mannito", "grow_cycle_action", { ...area, action: "confirm_phase" });
    });
    action("firmware", () => {
      const fw = this._hass.states[this._info.board_entities.firmware];
      if (fw && confirm(this._text(t.installConfirm, { v: fw.attributes.latest_version }))) {
        this._call("update", "install", {}, { entity_id: this._info.board_entities.firmware });
      }
    });
  }

  // ---------------------------------------------------------------------------------------------------------- update

  _set(bind, text) {
    const el = this.shadowRoot.querySelector(`[data-bind="${bind}"]`);
    if (el && el.textContent !== text) el.textContent = text;
    return el;
  }

  _update() {
    if (!this._hass || !this._info) return;
    const t = this._t;
    const root = this.shadowRoot;
    const active = root.activeElement;

    // header
    const statusObj = this._entity("status");
    const status = statusObj?.state;
    const chip = this._set("status", t.status[status] || "–");
    if (chip) chip.className = `chip ${status || "nodata"}`;
    const phase = this._entity("grow_phase");
    const parts = [];
    if (phase && !BAD.has(phase.state)) parts.push(phase.state);
    const day = this._num("day_of_grow");
    if (day !== null) parts.push(`${t.dayOfGrow} ${day}`);
    const phaseDay = this._num("day_of_phase");
    if (phaseDay !== null) parts.push(`${t.phaseDay} ${phaseDay}`);
    this._set("sub", parts.join(" · "));
    const emergency = this._entity("emergency");
    const banner = root.querySelector('[data-bind="emergency"]');
    if (banner) {
      const headline = this._entity("headline");
      banner.hidden = emergency?.state !== "on";
      banner.textContent = headline && !BAD.has(headline.state) ? headline.state : t.emergencyMode;
    }
    const isDay = this._entity("day")?.state === "on";
    const lightEl = root.querySelector('[data-bind="light"]');
    if (lightEl) {
      lightEl.innerHTML = `<ha-icon icon="${isDay ? "mdi:white-balance-sunny" : "mdi:weather-night"}"></ha-icon><span>${esc(isDay ? t.day : t.night)}</span>`;
      lightEl.classList.toggle("is-day", isDay);
    }

    // climate tiles
    for (const c of CLIMATE) {
      if (!this._info.entities[c.key]) continue;
      this._set(`v-${c.key}`, this._fmt(this._entity(c.key)));
      if (c.target) {
        const current = this._num(c.key);
        const target = this._num(c.target);
        this._set(`t-${c.key}`, target === null ? "" : `${t.target} ${this._fmt(this._entity(c.target))}`);
        const dot = root.querySelector(`[data-bind="d-${c.key}"]`);
        if (dot) {
          if (current === null || target === null) {
            dot.style.display = "none";
          } else {
            const deviation = (current - target) / (c.tolerance * 2);
            dot.style.display = "";
            dot.style.left = `${50 + Math.max(-1, Math.min(1, deviation)) * 46}%`;
            const ratio = Math.abs(current - target) / c.tolerance;
            dot.className = `dev-dot ${ratio <= 1 ? "ok" : ratio <= 2 ? "warn" : "bad"}`;
          }
        }
      } else if (c.second) {
        this._set(`s-${c.key}`, this._fmt(this._entity(c.second), ""));
      }
    }

    // irrigation
    if (this._info.entities.substrate_moisture) {
      const irrPhase = this._entity("irrigation_phase")?.state;
      const phaseText = irrPhase && !BAD.has(irrPhase) ? t[irrPhase.toLowerCase()] || irrPhase : "–";
      const pc = this._set("irr-phase", phaseText);
      if (pc) pc.className = `phase-chip ${BAD.has(irrPhase) ? "" : (irrPhase || "").toLowerCase()}`;
      const vwc = this._num("substrate_moisture");
      const peak = this._num("substrate_peak");
      const fc = this._num("field_capacity");
      const dryback = this._num("p2_dryback");
      const minVwc = this._num("min_vwc");
      this._set("vwc", this._fmt(this._entity("substrate_moisture")));
      const top = Math.max(60, Math.ceil(((fc ?? vwc ?? 50) * 1.25) / 10) * 10);
      const pos = (v) => `${Math.max(0, Math.min(100, (v / top) * 100))}%`;
      const fill = root.querySelector('[data-bind="vwc-fill"]');
      if (fill) fill.style.width = vwc === null ? "0%" : pos(vwc);
      const mark = (bind, value) => {
        const el = root.querySelector(`[data-bind="${bind}"]`);
        if (!el) return;
        el.style.display = value === null || value <= 0 ? "none" : "";
        if (value !== null) el.style.left = pos(value);
      };
      mark("m-peak", peak);
      mark("m-fc", fc);
      mark("m-trigger", peak !== null && dryback !== null ? peak - dryback : null);
      mark("m-min", minVwc);
      const legend = [];
      if (peak !== null) legend.push(`<span class="lg peak"></span>${esc(t.peak)} ${this._fmtNumber(peak, 1)} %`);
      if (fc !== null) legend.push(`<span class="lg fc"></span>${esc(t.fieldCapacity)} ${this._fmtNumber(fc, 1)} %`);
      if (peak !== null && dryback !== null) legend.push(`<span class="lg trigger"></span>${esc(t.trigger)} ${this._fmtNumber(peak - dryback, 1)} %`);
      if (minVwc) legend.push(`<span class="lg emergency"></span>${esc(t.emergencyLine)} ${this._fmtNumber(minVwc, 1)} %`);
      const legendEl = root.querySelector('[data-bind="legend"]');
      if (legendEl && legendEl.dataset.html !== legend.join("")) {
        legendEl.innerHTML = legend.map((l) => `<span class="lg-item">${l}</span>`).join("");
        legendEl.dataset.html = legend.join("");
      }
      this._set("shots", this._num("shots_today") === null ? "–" : String(this._num("shots_today")));
      this._set("water", this._num("water_today") === null ? "–" : this._fmtNumber(this._num("water_today"), 0));
      this._set("dryback", this._fmt(this._entity("dryback")));
      const next = this._num("next_shot");
      const last = this._relative(this._entity("last_shot")?.state);
      if (next !== null) {
        this._set("next", this._text(t.inMin, { n: next }));
        this._set("next-l", t.nextShot);
      } else {
        this._set("next", last || "–");
        this._set("next-l", t.lastShot);
      }
    }

    // tank
    if (this._info.entities.tank_volume) {
      const liters = this._num("tank_volume");
      const percent = this._num("tank_level");
      this._set("tank-text", liters === null ? "–" : `${this._fmtNumber(liters, 1)} l${percent === null ? "" : ` · ${percent} %`}`);
      const tankFill = root.querySelector('[data-bind="tank-fill"]');
      if (tankFill) {
        tankFill.style.width = `${percent ?? 0}%`;
        tankFill.className = `bar-fill ${percent !== null && percent < 20 ? "bad" : percent !== null && percent < 35 ? "warn" : ""}`;
      }
    }

    // devices
    for (const o of this._info.outputs || []) {
      const control = o.entities.control ? this._hass.states[o.entities.control] : undefined;
      const stateObj = control || (o.entities.on ? this._hass.states[o.entities.on] : undefined);
      const manual = o.entities.manual_override ? this._hass.states[o.entities.manual_override]?.state === "on" : false;
      const badge = root.querySelector(`[data-bind="manual-${o.device_id}"]`);
      if (badge) badge.hidden = !manual;
      const row = root.querySelector(`[data-device="${o.device_id}"]`);
      if (!row) continue;
      const isOn = stateObj ? ["on", "open", "opening"].includes(stateObj.state) : false;
      row.classList.toggle("on", isOn);
      row.classList.toggle("unavailable", !stateObj || stateObj.state === "unavailable");
      let level = null;
      if (control?.attributes?.percentage !== undefined && control.attributes.percentage !== null) level = control.attributes.percentage;
      else if (control?.attributes?.brightness !== undefined && control.attributes.brightness !== null) level = Math.round((control.attributes.brightness / 255) * 100);
      const stateText = o.type === "valve" ? (isOn ? t.opened : t.closed) : isOn ? (o.dimmable && level ? `${level} %` : t.on) : t.off;
      this._set(`state-${o.device_id}`, stateText);
      const toggle = row.querySelector(`[data-toggle="${o.device_id}"]`);
      if (toggle && toggle !== active) toggle.checked = isOn;
      const slider = row.querySelector(`[data-level="${o.device_id}"]`);
      if (slider && slider !== active && level !== null) slider.value = String(level);
    }

    // settings
    for (const el of root.querySelectorAll("[data-select]")) {
      const stateObj = this._entity(el.dataset.select);
      if (!stateObj || el === active) continue;
      const options = stateObj.attributes.options || [];
      const signature = options.join("|");
      if (el.dataset.options !== signature) {
        el.innerHTML = options
          .map((option) => `<option value="${esc(option)}">${esc(this._hass.formatEntityState ? this._hass.formatEntityState(stateObj, option) : option)}</option>`)
          .join("");
        el.dataset.options = signature;
      }
      el.value = stateObj.state;
      el.disabled = stateObj.state === "unavailable";
    }
    for (const el of root.querySelectorAll("[data-number]")) {
      const stateObj = this._entity(el.dataset.number);
      if (!stateObj) continue;
      this._set(`u-${el.dataset.number}`, stateObj.attributes.unit_of_measurement || "");
      if (el === active) continue;
      el.min = stateObj.attributes.min;
      el.max = stateObj.attributes.max;
      el.step = stateObj.attributes.step;
      el.value = BAD.has(stateObj.state) ? "" : stateObj.state;
    }
    for (const p of this._info.plants || []) {
      const height = p.entities.height ? this._hass.states[p.entities.height] : undefined;
      this._set(`ph-${p.plant_id}`, this._fmt(height));
      const measured = p.entities.measured ? this._hass.states[p.entities.measured]?.state : undefined;
      const ago = this._relative(measured);
      this._set(`pm-${p.plant_id}`, ago ? this._text(t.measuredAgo, { t: ago }) : t.notMeasured);
    }
    const problems = this._num("open_problems");
    this._set("problems", problems ? (problems === 1 ? t.openProblem : this._text(t.openProblems, { n: problems })) : "");
    const lightsOn = root.querySelector('[data-time="lights_on"]');
    const lightsOnState = this._entity("lights_on")?.state;
    if (lightsOn && lightsOn !== active && lightsOnState && !BAD.has(lightsOnState)) lightsOn.value = lightsOnState.slice(0, 5);
    const areaControl = root.querySelector("[data-area-control]");
    if (areaControl && areaControl !== active) areaControl.checked = this._entity("control")?.state === "on";
    const fwId = this._info.board_entities?.firmware;
    if (fwId) {
      const fw = this._hass.states[fwId];
      const installed = fw?.attributes?.installed_version;
      const latest = fw?.attributes?.latest_version;
      const update = fw?.state === "on";
      this._set("fw-text", update ? `${installed || "–"} → ${latest}` : `${installed || "–"} · ${t.upToDate}`);
      const button = root.querySelector('[data-action="firmware"]');
      if (button) button.hidden = !(update && (fw.attributes.supported_features & 1) && !fw.attributes.in_progress);
    }
  }
}

const STYLE = `<style>
  :host { --m-radius: 12px; --m-gap: 12px; --m-accent: var(--primary-color); --m-ok: var(--success-color, #43a047);
          --m-warn: var(--warning-color, #ffa000); --m-bad: var(--error-color, #db4437); --m-soft: var(--secondary-background-color, rgba(127,127,127,.08)); }
  ha-card { padding: 16px; overflow: hidden; }
  .empty { display: flex; gap: 12px; align-items: center; color: var(--secondary-text-color); padding: 8px 0; }
  .empty.error { color: var(--m-bad); }
  .empty.small { font-size: .9em; }
  .header { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
  .title-row { display: flex; align-items: center; gap: 12px; }
  .title-icon { --mdc-icon-size: 28px; color: var(--m-accent); background: color-mix(in srgb, var(--m-accent) 14%, transparent);
                border-radius: 50%; padding: 8px; }
  .title { flex: 1; min-width: 0; }
  .name { font-size: 1.25em; font-weight: 600; line-height: 1.2; }
  .sub { color: var(--secondary-text-color); font-size: .9em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .chip { padding: 4px 10px; border-radius: 999px; font-size: .8em; font-weight: 600; white-space: nowrap; background: var(--m-soft); }
  .chip.ok { color: var(--m-ok); background: color-mix(in srgb, var(--m-ok) 15%, transparent); }
  .chip.attention { color: var(--m-warn); background: color-mix(in srgb, var(--m-warn) 18%, transparent); }
  .chip.problem { color: var(--m-bad); background: color-mix(in srgb, var(--m-bad) 15%, transparent); }
  .chip.neutral, .chip.nodata { color: var(--secondary-text-color); }
  .banner { background: color-mix(in srgb, var(--m-bad) 15%, transparent); color: var(--m-bad); border-radius: 8px; padding: 8px 12px; font-weight: 500; }
  .light-row { display: inline-flex; align-items: center; gap: 6px; font-size: .85em; color: var(--secondary-text-color); }
  .light-row ha-icon { --mdc-icon-size: 18px; }
  .light-row.is-day ha-icon { color: #f9a825; }
  .tabs { display: flex; gap: 4px; background: var(--m-soft); border-radius: 10px; padding: 4px; margin-bottom: 14px; }
  .tab { flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px; border: 0; background: transparent; color: var(--secondary-text-color);
         padding: 8px; border-radius: 8px; font: inherit; font-size: .9em; cursor: pointer; }
  .tab ha-icon { --mdc-icon-size: 18px; }
  .tab.active { background: var(--card-background-color, #fff); color: var(--primary-text-color); box-shadow: 0 1px 3px rgba(0,0,0,.12); font-weight: 600; }
  .section-title { font-size: .75em; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--secondary-text-color); margin: 16px 0 8px; }
  .pane > .section-title:first-child { margin-top: 0; }
  .row-between { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
  .muted { color: var(--secondary-text-color); }
  .small { font-size: .85em; }
  .hint { margin: -4px 0 8px; }
  .tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: var(--m-gap); }
  .tile { all: unset; cursor: pointer; background: var(--m-soft); border-radius: var(--m-radius); padding: 12px; display: flex; flex-direction: column; gap: 4px; }
  .tile:hover { background: color-mix(in srgb, var(--m-accent) 8%, var(--m-soft)); }
  .tile-head { display: flex; align-items: center; gap: 6px; color: var(--secondary-text-color); font-size: .8em; }
  .tile-head ha-icon { --mdc-icon-size: 16px; }
  .tile-value { font-size: 1.5em; font-weight: 600; white-space: nowrap; }
  .tile-target { color: var(--secondary-text-color); font-size: .8em; min-height: 1.1em; }
  .dev { position: relative; height: 6px; border-radius: 3px; margin-top: 6px;
         background: linear-gradient(90deg, color-mix(in srgb, var(--m-bad) 35%, transparent), color-mix(in srgb, var(--m-ok) 35%, transparent) 35%, color-mix(in srgb, var(--m-ok) 35%, transparent) 65%, color-mix(in srgb, var(--m-bad) 35%, transparent)); }
  .dev-mid { position: absolute; left: 50%; top: -2px; bottom: -2px; width: 2px; background: var(--secondary-text-color); opacity: .5; }
  .dev-dot { position: absolute; top: 50%; width: 12px; height: 12px; border-radius: 50%; transform: translate(-50%, -50%); border: 2px solid var(--card-background-color, #fff); transition: left .4s; }
  .dev-dot.ok { background: var(--m-ok); } .dev-dot.warn { background: var(--m-warn); } .dev-dot.bad { background: var(--m-bad); }
  .phase-chip { text-transform: none; letter-spacing: 0; font-weight: 600; font-size: 1.1em; padding: 2px 10px; border-radius: 999px; background: var(--m-soft); color: var(--primary-text-color); }
  .phase-chip.p1 { background: color-mix(in srgb, #1e88e5 18%, transparent); color: #1e88e5; }
  .phase-chip.p2 { background: color-mix(in srgb, var(--m-ok) 18%, transparent); color: var(--m-ok); }
  .phase-chip.p3, .phase-chip.p0 { background: color-mix(in srgb, #7e57c2 18%, transparent); color: #7e57c2; }
  .moisture { background: var(--m-soft); border-radius: var(--m-radius); padding: 12px; cursor: pointer; }
  .moisture-head { display: flex; justify-content: space-between; align-items: baseline; color: var(--secondary-text-color); font-size: .85em; }
  .big { font-size: 1.6em; font-weight: 600; color: var(--primary-text-color); }
  .scale { position: relative; height: 14px; border-radius: 7px; background: color-mix(in srgb, var(--secondary-text-color) 15%, transparent); margin: 10px 0 8px; }
  .fill { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 7px; background: linear-gradient(90deg, #64b5f6, #1e88e5); transition: width .4s; }
  .mark { position: absolute; top: -4px; bottom: -4px; width: 3px; border-radius: 2px; transform: translateX(-50%); }
  .mark.peak, .lg.peak { background: #0d47a1; } .mark.fc, .lg.fc { background: var(--m-ok); }
  .mark.trigger, .lg.trigger { background: var(--m-warn); } .mark.emergency, .lg.emergency { background: var(--m-bad); }
  .legend { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: .78em; color: var(--secondary-text-color); }
  .lg-item { display: inline-flex; align-items: center; gap: 5px; }
  .lg { display: inline-block; width: 10px; height: 10px; border-radius: 2px; }
  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: var(--m-gap); }
  .stat { background: var(--m-soft); border-radius: var(--m-radius); padding: 10px; text-align: center; }
  .stat-v { font-size: 1.15em; font-weight: 600; white-space: nowrap; }
  .stat-l { font-size: .72em; color: var(--secondary-text-color); margin-top: 2px; }
  .bar { height: 12px; border-radius: 6px; background: color-mix(in srgb, var(--secondary-text-color) 15%, transparent); overflow: hidden; cursor: pointer; }
  .bar-fill { height: 100%; border-radius: 6px; background: linear-gradient(90deg, #26a69a, #00897b); transition: width .4s; }
  .bar-fill.warn { background: var(--m-warn); } .bar-fill.bad { background: var(--m-bad); }
  .actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
  .btn { display: inline-flex; align-items: center; gap: 6px; border: 0; border-radius: 10px; padding: 9px 14px; font: inherit; font-size: .9em; font-weight: 600;
         background: var(--m-accent); color: var(--text-primary-color, #fff); cursor: pointer; }
  .btn ha-icon { --mdc-icon-size: 18px; }
  .btn.small { padding: 6px 10px; font-size: .82em; }
  .btn.ghost { background: var(--m-soft); color: var(--primary-text-color); }
  .btn:hover { filter: brightness(1.08); }
  .device-list { display: flex; flex-direction: column; gap: 8px; }
  .device { display: flex; align-items: center; gap: 12px; background: var(--m-soft); border-radius: var(--m-radius); padding: 8px 10px; }
  .device.unavailable { opacity: .5; }
  .dev-icon { all: unset; cursor: pointer; display: grid; place-items: center; width: 38px; height: 38px; border-radius: 50%;
              background: color-mix(in srgb, var(--secondary-text-color) 15%, transparent); color: var(--secondary-text-color); flex: none; }
  .device.on .dev-icon { background: color-mix(in srgb, var(--m-accent) 20%, transparent); color: var(--m-accent); }
  .dev-name { flex: 1; min-width: 0; }
  .dev-name > div:first-child { font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .dev-controls { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
  .badge { font-size: .72em; font-weight: 700; padding: 2px 8px; border-radius: 999px; }
  .badge.manual { background: color-mix(in srgb, var(--m-warn) 20%, transparent); color: var(--m-warn); }
  .icon-btn { all: unset; cursor: pointer; display: grid; place-items: center; width: 32px; height: 32px; border-radius: 50%; color: var(--secondary-text-color); }
  .icon-btn:hover { background: color-mix(in srgb, var(--m-accent) 12%, transparent); color: var(--m-accent); }
  .slider { width: 110px; accent-color: var(--m-accent); }
  .toggle { position: relative; display: inline-block; width: 40px; height: 22px; flex: none; }
  .toggle input { opacity: 0; width: 0; height: 0; }
  .toggle span { position: absolute; inset: 0; border-radius: 11px; background: color-mix(in srgb, var(--secondary-text-color) 35%, transparent); transition: .2s; cursor: pointer; }
  .toggle span::before { content: ""; position: absolute; width: 16px; height: 16px; left: 3px; top: 3px; border-radius: 50%; background: #fff; transition: .2s; }
  .toggle input:checked + span { background: var(--m-accent); }
  .toggle input:checked + span::before { transform: translateX(18px); }
  .settings-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }
  .field { display: flex; flex-direction: column; gap: 6px; background: var(--m-soft); border-radius: var(--m-radius); padding: 10px 12px; font-size: .85em; color: var(--secondary-text-color); }
  .field select, .field input { font: inherit; font-size: 1.05em; color: var(--primary-text-color); background: var(--card-background-color, #fff);
                                border: 1px solid var(--divider-color, rgba(127,127,127,.3)); border-radius: 8px; padding: 6px 8px; min-width: 0; }
  .num-wrap, .inline { display: flex; align-items: center; gap: 6px; }
  .num-wrap input { flex: 1; width: 100%; }
  .inline input[type=number] { width: 60px; }
  .unit { color: var(--secondary-text-color); white-space: nowrap; }
  .timeline { margin: -2px 0 14px; }
  .tl-bar { position: relative; height: 22px; border-radius: 6px; background: var(--m-soft); overflow: hidden; }
  .tl-seg { position: absolute; top: 0; bottom: 0; display: flex; align-items: center; padding: 0 6px; box-sizing: border-box; overflow: hidden;
            border-right: 2px solid var(--card-background-color, #fff); font-size: .7em; white-space: nowrap; color: var(--secondary-text-color); }
  .tl-seg.done { background: color-mix(in srgb, var(--m-ok) 18%, transparent); }
  .tl-seg.current { background: color-mix(in srgb, var(--m-accent) 30%, transparent); color: var(--primary-text-color); font-weight: 600; }
  .tl-seg.planned { background: color-mix(in srgb, var(--secondary-text-color) 10%, transparent); }
  .tl-seg span { overflow: hidden; text-overflow: ellipsis; }
  .tl-now { position: absolute; top: -2px; bottom: -2px; width: 2px; background: var(--m-bad); }
  .tank-book { margin-top: 8px; flex-wrap: wrap; }
  .tank-book input { width: 70px; font: inherit; padding: 5px 8px; border-radius: 8px; border: 1px solid var(--divider-color, rgba(127,127,127,.3));
                     background: var(--card-background-color, #fff); color: var(--primary-text-color); }
  .plants { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: var(--m-gap); }
  .plant { background: var(--m-soft); border-radius: var(--m-radius); padding: 12px; display: flex; flex-direction: column; gap: 10px; }
  .plant-head { display: flex; align-items: center; gap: 10px; }
  .plant-head > ha-icon { color: var(--m-ok); background: color-mix(in srgb, var(--m-ok) 15%, transparent); border-radius: 50%; padding: 6px; }
  .plant-title { flex: 1; min-width: 0; }
  .plant-name { font-weight: 600; }
  .plant-height { all: unset; cursor: pointer; display: flex; flex-direction: column; align-items: flex-end; }
  .plant-actions input, .plant-actions select { font: inherit; font-size: .9em; padding: 5px 8px; border-radius: 8px; min-width: 0;
                                                border: 1px solid var(--divider-color, rgba(127,127,127,.3)); background: var(--card-background-color, #fff); color: var(--primary-text-color); }
  .plant-actions input[type=number] { width: 90px; }
  .note-input { font: inherit; font-size: .9em; padding: 6px 8px; border-radius: 8px; border: 1px solid var(--divider-color, rgba(127,127,127,.3));
                background: var(--card-background-color, #fff); color: var(--primary-text-color); width: 100%; box-sizing: border-box; }
  .plant-actions .push { margin-left: auto; }
  .plant-actions select { flex: 1; min-width: 100px; }
  .check { display: inline-flex; align-items: center; gap: 4px; font-size: .8em; color: var(--secondary-text-color); white-space: nowrap; }
  @media (max-width: 480px) { .stats { grid-template-columns: repeat(2, 1fr); } .slider { width: 80px; } }
</style>`;

if (!customElements.get("mannito-card")) {
  customElements.define("mannito-card", MannitoCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "mannito-card",
    name: "Mannito grow area",
    description: "Climate, irrigation, plants, devices and settings of one grow area on a Mannito board.",
    preview: false,
    documentationURL: "https://github.com/mannito-farming-solutions/mannito-homeassistant",
  });
  console.info(`%c MANNITO-CARD %c ${CARD_VERSION} `, "color:#fff;background:#43a047;font-weight:700", "color:#43a047;background:#fff");
}
