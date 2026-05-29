const apiBase = "";

let state = {
  loading: true,
  error: "",
  notice: "",
  health: "unknown",
  projectName: "No project",
  specs: [],
  tabs: [
    {
      id: "schematic-1",
      title: "Schematic 1",
      kind: "schematic",
      path: "schematic-1.json",
      diagram: emptyDiagram()
    }
  ],
  activeTabId: "schematic-1",
  pendingClassPath: null,
  selectedDeviceId: null,
  outputMode: "bottom",
  outputCollapsed: false
};

async function request(path, options = {}) {
  const response = await fetch(`${apiBase}${path}`, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers
    }
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json();
}

async function readError(response) {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // Fall through to the HTTP status if the response is not JSON.
  }
  return `Request failed with ${response.status} ${response.statusText}`;
}

function emptyDiagram() {
  return { version: 1, devices: [], connections: [] };
}

function activeTab() {
  return (
    state.tabs.find((tab) => tab.id === state.activeTabId) || state.tabs[0]
  );
}

function activeDiagram() {
  return activeTab()?.diagram || emptyDiagram();
}

function pendingSpec() {
  return state.specs.find((spec) => spec.class_path === state.pendingClassPath);
}

function selectedDevice() {
  return activeDiagram().devices.find(
    (device) => device.id === state.selectedDeviceId
  );
}

function specFor(classPath) {
  return state.specs.find((spec) => spec.class_path === classPath);
}

function setState(nextState) {
  state = { ...state, ...nextState };
  render();
}

function updateActiveTab(patch) {
  setState({
    tabs: state.tabs.map((tab) =>
      tab.id === state.activeTabId ? { ...tab, ...patch } : tab
    )
  });
}

function updateActiveDiagram(diagram) {
  updateActiveTab({ diagram });
}

function groupByCategory(specs) {
  const grouped = new Map();
  for (const spec of specs) {
    const category = spec.category || "Uncategorized";
    grouped.set(category, [...(grouped.get(category) || []), spec]);
  }
  return [...grouped.entries()].sort(([left], [right]) =>
    left.localeCompare(right)
  );
}

function defaultProperties(spec) {
  return Object.fromEntries(
    Object.entries(spec.properties || {})
      .filter(([, property]) => "default" in property || "value" in property)
      .map(([name, property]) => [
        name,
        "default" in property ? property.default : property.value
      ])
  );
}

function nextDeviceId(spec, diagram) {
  const fallback = spec.class_path.split(".").at(-1) || "device";
  const base = toSnakeCase(spec.gui_name || fallback);
  const used = new Set(diagram.devices.map((device) => device.id));
  let index = diagram.devices.length + 1;
  let id = `${base}_${index}`;
  while (used.has(id)) {
    index += 1;
    id = `${base}_${index}`;
  }
  return id;
}

function toSnakeCase(value) {
  return value
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .replace(/[^a-zA-Z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .toLowerCase();
}

function formatValue(value) {
  if (value === null || value === undefined) {
    return "null";
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value);
}

function render() {
  const app = document.getElementById("app");
  if (!app) {
    return;
  }

  app.innerHTML = `
    <main class="appShell">
      ${renderToolbar()}
      <div class="workspaceShell">
        ${renderPalette()}
        ${renderWorkspace()}
        ${renderInspector()}
      </div>
    </main>
  `;
  bindEvents();
}

function renderToolbar() {
  const online = state.health === "ok" ? "online" : "";
  return `
    <header class="toolbar">
      <div class="projectStatus">
        <strong>${escapeHtml(state.projectName)}</strong>
        <span class="${online}">Server: ${escapeHtml(state.health)}</span>
      </div>
      <nav class="toolbarActions" aria-label="Project actions">
        <button id="open-diagram" type="button">Open</button>
        <button id="save-diagram" type="button">Save</button>
        <button id="new-schematic" type="button">New schematic</button>
        <button type="button">Generate script</button>
        <button type="button">Run simulation</button>
      </nav>
    </header>
  `;
}

function renderPalette() {
  return `
    <aside class="leftSidebar" aria-label="Device palette">
      <div class="panelHeader">
        <h2>Device palette</h2>
        <span>${state.specs.length}</span>
      </div>
      ${renderPaletteBody()}
    </aside>
  `;
}

function renderPaletteBody() {
  if (state.error) {
    return `
      <section class="notice" role="alert">
        <strong>Message</strong>
        <p>${escapeHtml(state.error)}</p>
        <button id="retry" type="button">Retry</button>
      </section>
    `;
  }
  if (state.loading) {
    return '<section class="empty">Loading specs...</section>';
  }
  if (state.specs.length === 0) {
    return '<section class="empty">No generated specs found.</section>';
  }
  return `
    ${state.notice ? `<section class="notice compact"><p>${escapeHtml(state.notice)}</p></section>` : ""}
    <div class="paletteGroups">
      ${groupByCategory(state.specs)
        .map(([category, specs]) => renderPaletteGroup(category, specs))
        .join("")}
    </div>
  `;
}

function renderPaletteGroup(category, specs) {
  return `
    <section class="paletteGroup">
      <h3>${escapeHtml(category)}</h3>
      ${specs.map((spec) => renderPaletteDevice(spec)).join("")}
    </section>
  `;
}

function renderPaletteDevice(spec) {
  const active = spec.class_path === state.pendingClassPath ? "active" : "";
  return `
    <button
      class="paletteDevice ${active}"
      data-palette-class-path="${escapeHtml(spec.class_path)}"
      type="button"
    >
      <div>
        <strong>${escapeHtml(spec.gui_name || spec.class_path)}</strong>
        <small>${escapeHtml(spec.icon || "no icon")}</small>
      </div>
      <span>${Object.keys(spec.properties || {}).length}</span>
    </button>
  `;
}

function renderWorkspace() {
  return `
    <section class="centerPane" aria-label="Workspace">
      <div class="tabs" role="tablist" aria-label="Open editors">
        ${state.tabs.map(renderTab).join("")}
      </div>
      <div class="editorArea">${renderActiveEditor()}</div>
      ${renderOutputDock()}
    </section>
  `;
}

function renderTab(tab) {
  const active = tab.id === state.activeTabId ? "active" : "";
  return `
    <button
      class="${active}"
      data-tab-id="${escapeHtml(tab.id)}"
      type="button"
      role="tab"
      aria-selected="${tab.id === state.activeTabId}"
    >
      ${escapeHtml(tab.title)}
    </button>
  `;
}

function renderActiveEditor() {
  const tab = activeTab();
  if (!tab) {
    return "";
  }
  if (tab.kind === "output") {
    return `
      <section class="outputEditor">
        <h2>Simulation Output</h2>
        <p>Validation, generated scripts, logs, and results appear here.</p>
        <button id="dock-output" type="button">Dock to bottom</button>
      </section>
    `;
  }
  return renderSchematicEditorWrapper(tab);
}

function renderSchematicEditorWrapper(tab) {
  const spec = pendingSpec();
  const placing = spec ? "placing" : "";
  const diagram = tab.diagram || emptyDiagram();
  return `
    <section class="schematicEditor" aria-label="${escapeHtml(tab.title)} editor">
      <button class="placementStatus ${placing}" type="button">
        ${spec ? `Place ${escapeHtml(spec.gui_name || spec.class_path)}` : "Select a device from the palette"}
      </button>
      <div
        id="schematic-surface"
        class="schematicSurface ${placing}"
        role="button"
        tabindex="0"
      >
        ${diagram.devices.length === 0 ? renderSchematicPlaceholder(tab.title) : ""}
        ${diagram.devices.map(renderDeviceNode).join("")}
      </div>
    </section>
  `;
}

function renderSchematicPlaceholder(title) {
  return `
    <div class="schematicPlaceholder">
      <h2>${escapeHtml(title)}</h2>
      <p>Click a palette device, then click here to place it.</p>
    </div>
  `;
}

function renderDeviceNode(device) {
  const spec = specFor(device.type);
  const selected = device.id === state.selectedDeviceId ? "selected" : "";
  return `
    <button
      class="deviceNode ${selected}"
      data-device-id="${escapeHtml(device.id)}"
      style="left: ${device.position.x}px; top: ${device.position.y}px;"
      type="button"
    >
      <strong>${escapeHtml(spec?.gui_name || device.type)}</strong>
      <span>${escapeHtml(spec?.icon || "no icon")}</span>
    </button>
  `;
}

function renderOutputDock() {
  const outputTabOpen = state.tabs.some((tab) => tab.kind === "output");
  if (state.outputMode === "tab" && outputTabOpen) {
    return `
      <button id="restore-output" class="restoreOutput" type="button">
        Restore output panel
      </button>
    `;
  }
  const collapsed = state.outputCollapsed ? "collapsed" : "";
  return `
    <section class="bottomPanel ${collapsed}">
      <div class="bottomPanelHeader">
        <div>
          <strong>Simulation output</strong>
          <span>Validation, script generation, logs, results</span>
        </div>
        <div class="bottomPanelActions">
          <button id="toggle-output" type="button">
            ${state.outputCollapsed ? "Expand" : "Collapse"}
          </button>
          <button id="output-as-tab" type="button">Open as tab</button>
        </div>
      </div>
      ${state.outputCollapsed ? "" : renderOutputContent()}
    </section>
  `;
}

function renderOutputContent() {
  return `
    <div class="outputContent">
      <p>No simulation output yet.</p>
    </div>
  `;
}

function renderInspector() {
  const device = selectedDevice();
  return `
    <aside class="rightSidebar" aria-label="Inspector">
      <div class="panelHeader"><h2>Inspector</h2></div>
      ${device ? renderDeviceInspector(device) : renderEmptyInspector()}
    </aside>
  `;
}

function renderEmptyInspector() {
  return `
    <section class="inspectorPlaceholder">
      <strong>Selected item</strong>
      <p>No device, port, or connection selected.</p>
    </section>
  `;
}

function renderDeviceInspector(device) {
  const spec = specFor(device.type);
  return `
    <section class="specPreview">
      <h3>${escapeHtml(spec?.gui_name || device.type)}</h3>
      <dl>
        <dt>Device id</dt>
        <dd>${escapeHtml(device.id)}</dd>
        <dt>Type</dt>
        <dd>${escapeHtml(device.type)}</dd>
        <dt>Icon</dt>
        <dd>${escapeHtml(spec?.icon || "none")}</dd>
      </dl>
      <h4>Properties</h4>
      ${renderPropertyList(device.properties || {})}
    </section>
  `;
}

function renderPropertyList(properties) {
  const entries = Object.entries(properties);
  if (entries.length === 0) {
    return '<p class="muted">No properties</p>';
  }
  return `
    <ul class="propertyList">
      ${entries
        .map(([name, value]) => `
          <li>
            <span>${escapeHtml(name)}</span>
            <small>${escapeHtml(formatValue(value))}</small>
          </li>
        `)
        .join("")}
    </ul>
  `;
}

function bindEvents() {
  bind("retry", load);
  bind("new-schematic", addSchematicTab);
  bind("open-diagram", openDiagram);
  bind("save-diagram", saveActiveDiagram);
  bind("dock-output", showOutputInBottomPanel);
  bind("restore-output", showOutputInBottomPanel);
  bind("toggle-output", () =>
    setState({ outputCollapsed: !state.outputCollapsed })
  );
  bind("output-as-tab", showOutputAsTab);

  for (const button of document.querySelectorAll("[data-tab-id]")) {
    button.addEventListener("click", () =>
      setState({
        activeTabId: button.getAttribute("data-tab-id"),
        selectedDeviceId: null
      })
    );
  }
  for (const button of document.querySelectorAll("[data-palette-class-path]")) {
    button.addEventListener("click", () =>
      setState({
        pendingClassPath: button.getAttribute("data-palette-class-path"),
        selectedDeviceId: null
      })
    );
  }
  for (const button of document.querySelectorAll("[data-device-id]")) {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      setState({
        selectedDeviceId: button.getAttribute("data-device-id"),
        pendingClassPath: null
      });
    });
  }
  const surface = document.getElementById("schematic-surface");
  if (surface) {
    surface.addEventListener("click", placeOnSurface);
  }
}

function bind(id, handler) {
  const element = document.getElementById(id);
  if (element) {
    element.addEventListener("click", handler);
  }
}

function addSchematicTab() {
  const number =
    state.tabs.filter((tab) => tab.kind === "schematic").length + 1;
  const tab = {
    id: `schematic-${Date.now()}`,
    title: `Schematic ${number}`,
    kind: "schematic",
    path: `schematic-${number}.json`,
    diagram: emptyDiagram()
  };
  setState({
    tabs: [...state.tabs, tab],
    activeTabId: tab.id,
    selectedDeviceId: null
  });
}

async function openDiagram() {
  const path = window.prompt("Diagram path", activeTab()?.path || "demo.json");
  if (!path) {
    return;
  }
  try {
    const result = await request(
      `/diagrams/load?${new URLSearchParams({ path }).toString()}`
    );
    const title = path.replace(/\.json$/i, "") || "Diagram";
    const tab = {
      id: `diagram-${Date.now()}`,
      title,
      kind: "schematic",
      path,
      diagram: result.diagram
    };
    setState({
      tabs: [...state.tabs, tab],
      activeTabId: tab.id,
      selectedDeviceId: null,
      notice: `Loaded ${path}`,
      error: ""
    });
  } catch (error) {
    setState({
      error: error instanceof Error ? error.message : "Unable to load diagram"
    });
  }
}

async function saveActiveDiagram() {
  const tab = activeTab();
  if (!tab?.diagram) {
    return;
  }
  const path = tab.path || window.prompt("Save diagram as", `${tab.title}.json`);
  if (!path) {
    return;
  }
  try {
    const result = await request("/diagrams/save", {
      method: "POST",
      body: JSON.stringify({ path, diagram: tab.diagram })
    });
    updateActiveTab({ path, diagram: result.diagram });
    setState({ notice: `Saved ${path}`, error: "" });
  } catch (error) {
    setState({
      error: error instanceof Error ? error.message : "Unable to save diagram"
    });
  }
}

function placeOnSurface(event) {
  if (!state.pendingClassPath) {
    setState({ selectedDeviceId: null });
    return;
  }
  const spec = pendingSpec();
  const tab = activeTab();
  if (!spec || !tab?.diagram) {
    return;
  }
  const rect = event.currentTarget.getBoundingClientRect();
  const device = {
    id: nextDeviceId(spec, tab.diagram),
    type: spec.class_path,
    position: {
      x: Math.round(event.clientX - rect.left),
      y: Math.round(event.clientY - rect.top)
    },
    properties: defaultProperties(spec)
  };
  updateActiveDiagram({
    ...tab.diagram,
    devices: [...tab.diagram.devices, device]
  });
  setState({
    selectedDeviceId: device.id,
    pendingClassPath: null
  });
}

function showOutputAsTab() {
  const existing = state.tabs.find((tab) => tab.kind === "output");
  if (existing) {
    setState({
      outputMode: "tab",
      outputCollapsed: true,
      activeTabId: existing.id
    });
    return;
  }
  const tab = {
    id: "simulation-output",
    title: "Simulation Output",
    kind: "output"
  };
  setState({
    tabs: [...state.tabs, tab],
    activeTabId: tab.id,
    outputMode: "tab",
    outputCollapsed: true
  });
}

function showOutputInBottomPanel() {
  const tabs = state.tabs.filter((tab) => tab.kind !== "output");
  const activeTabId = tabs.some((tab) => tab.id === state.activeTabId)
    ? state.activeTabId
    : tabs[0]?.id;
  setState({
    tabs,
    activeTabId,
    outputMode: "bottom",
    outputCollapsed: false
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function load() {
  setState({ loading: true, error: "", health: "unknown" });
  try {
    const [health, project, specs] = await Promise.all([
      request("/health"),
      request("/project"),
      request("/specs")
    ]);
    setState({
      loading: false,
      error: "",
      health: health.status,
      projectName: project.name,
      specs
    });
  } catch (error) {
    setState({
      loading: false,
      error: error instanceof Error ? error.message : "Unable to load GUI data",
      health: "unavailable",
      specs: []
    });
  }
}

render();
load();
