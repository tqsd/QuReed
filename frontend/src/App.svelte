<script lang="ts">
  import { onMount } from 'svelte';
  import {
    fetchHealth,
    fetchProject,
    fetchSpecs,
    loadDiagram,
    saveDiagram
  } from './api';
  import SchematicEditorWrapper from './SchematicEditorWrapper.svelte';
  import type {
    DeviceProperty,
    DeviceSpec,
    Diagram,
    DiagramDevice,
    OutputDockMode,
    WorkspaceTab
  } from './types';

  let specs: DeviceSpec[] = [];
  let loading = true;
  let error = '';
  let notice = '';
  let health = 'unknown';
  let projectName = 'No project';
  let outputCollapsed = false;
  let outputMode: OutputDockMode = 'bottom';
  let activeTabId = 'schematic-1';
  let pendingSpec: DeviceSpec | null = null;
  let selectedDeviceId: string | null = null;
  let tabs: WorkspaceTab[] = [
    {
      id: 'schematic-1',
      title: 'Schematic 1',
      kind: 'schematic',
      path: 'schematic-1.json',
      diagram: emptyDiagram()
    }
  ];

  $: groupedSpecs = groupByCategory(specs);
  $: specsByClassPath = new Map(specs.map((spec) => [spec.class_path, spec]));
  $: activeTab = tabs.find((tab) => tab.id === activeTabId) ?? tabs[0];
  $: activeDiagram = activeTab?.diagram ?? emptyDiagram();
  $: selectedDevice =
    activeDiagram.devices.find((device) => device.id === selectedDeviceId) ??
    null;
  $: selectedSpec = selectedDevice
    ? specsByClassPath.get(selectedDevice.type)
    : undefined;
  $: outputTabOpen = tabs.some((tab) => tab.kind === 'output');

  onMount(() => {
    void loadShell();
  });

  async function loadShell() {
    loading = true;
    error = '';

    try {
      const [healthResponse, projectResponse, specResponse] =
        await Promise.all([fetchHealth(), fetchProject(), fetchSpecs()]);
      health = healthResponse.status;
      projectName = projectResponse.name;
      specs = specResponse;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unable to load GUI data';
      specs = [];
      health = 'unavailable';
    } finally {
      loading = false;
    }
  }

  function emptyDiagram(): Diagram {
    return { version: 1, devices: [], connections: [] };
  }

  function addSchematicTab() {
    const number =
      tabs.filter((tab) => tab.kind === 'schematic').length + 1;
    const tab = {
      id: `schematic-${Date.now()}`,
      title: `Schematic ${number}`,
      kind: 'schematic' as const,
      path: `schematic-${number}.json`,
      diagram: emptyDiagram()
    };
    tabs = [...tabs, tab];
    activeTabId = tab.id;
    selectedDeviceId = null;
  }

  async function openDiagram() {
    const path = window.prompt('Diagram path', activeTab?.path ?? 'demo.json');
    if (!path) {
      return;
    }
    try {
      const result = await loadDiagram(path);
      const title = path.replace(/\.json$/i, '') || 'Diagram';
      const tab = {
        id: `diagram-${Date.now()}`,
        title,
        kind: 'schematic' as const,
        path,
        diagram: result.diagram
      };
      tabs = [...tabs, tab];
      activeTabId = tab.id;
      selectedDeviceId = null;
      notice = `Loaded ${path}`;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unable to load diagram';
    }
  }

  async function saveActiveDiagram() {
    if (!activeTab?.diagram) {
      return;
    }
    const path =
      activeTab.path ??
      window.prompt('Save diagram as', `${activeTab.title}.json`);
    if (!path) {
      return;
    }
    try {
      const result = await saveDiagram(path, activeTab.diagram);
      updateActiveTab({
        path,
        diagram: result.diagram
      });
      notice = `Saved ${path}`;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unable to save diagram';
    }
  }

  function selectPaletteDevice(spec: DeviceSpec) {
    pendingSpec = spec;
    selectedDeviceId = null;
  }

  function placeDevice(x: number, y: number) {
    if (!pendingSpec || !activeTab?.diagram) {
      return;
    }
    const device: DiagramDevice = {
      id: nextDeviceId(pendingSpec, activeTab.diagram),
      type: pendingSpec.class_path,
      position: { x: Math.round(x), y: Math.round(y) },
      properties: defaultProperties(pendingSpec)
    };
    updateActiveDiagram({
      ...activeTab.diagram,
      devices: [...activeTab.diagram.devices, device]
    });
    selectedDeviceId = device.id;
    pendingSpec = null;
  }

  function selectDevice(deviceId: string | null) {
    selectedDeviceId = deviceId;
    if (deviceId) {
      pendingSpec = null;
    }
  }

  function updateActiveDiagram(diagram: Diagram) {
    updateActiveTab({ diagram });
  }

  function updateActiveTab(patch: Partial<WorkspaceTab>) {
    tabs = tabs.map((tab) =>
      tab.id === activeTabId ? { ...tab, ...patch } : tab
    );
  }

  function nextDeviceId(spec: DeviceSpec, diagram: Diagram): string {
    const base = toSnakeCase(
      spec.gui_name || spec.class_path.split('.').at(-1) || 'device'
    );
    let index = diagram.devices.length + 1;
    let id = `${base}_${index}`;
    const used = new Set(diagram.devices.map((device) => device.id));
    while (used.has(id)) {
      index += 1;
      id = `${base}_${index}`;
    }
    return id;
  }

  function toSnakeCase(value: string): string {
    return value
      .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
      .replace(/[^a-zA-Z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')
      .toLowerCase();
  }

  function defaultProperties(spec: DeviceSpec): Record<string, unknown> {
    return Object.fromEntries(
      Object.entries(spec.properties)
        .filter(([, property]) => 'default' in property || 'value' in property)
        .map(([name, property]) => [
          name,
          'default' in property ? property.default : property.value
        ])
    );
  }

  function showOutputAsTab() {
    outputMode = 'tab';
    outputCollapsed = true;
    const existing = tabs.find((tab) => tab.kind === 'output');
    if (existing) {
      activeTabId = existing.id;
      return;
    }
    const tab = {
      id: 'simulation-output',
      title: 'Simulation Output',
      kind: 'output' as const
    };
    tabs = [...tabs, tab];
    activeTabId = tab.id;
  }

  function showOutputInBottomPanel() {
    outputMode = 'bottom';
    outputCollapsed = false;
    tabs = tabs.filter((tab) => tab.kind !== 'output');
    if (!tabs.some((tab) => tab.id === activeTabId)) {
      activeTabId = tabs[0]?.id ?? 'schematic-1';
    }
  }

  function groupByCategory(items: DeviceSpec[]) {
    const grouped = new Map<string, DeviceSpec[]>();
    for (const item of items) {
      const category = item.category || 'Uncategorized';
      grouped.set(category, [...(grouped.get(category) ?? []), item]);
    }
    return [...grouped.entries()].sort(([left], [right]) =>
      left.localeCompare(right)
    );
  }

  function propertyValue(property: DeviceProperty): string {
    if ('default' in property) {
      return formatValue(property.default);
    }
    if ('value' in property) {
      return formatValue(property.value);
    }
    return 'unset';
  }

  function formatValue(value: unknown): string {
    if (value === null || value === undefined) {
      return 'null';
    }
    if (typeof value === 'string') {
      return value;
    }
    return JSON.stringify(value);
  }
</script>

<main class="appShell">
  <header class="toolbar">
    <div class="projectStatus">
      <strong>{projectName}</strong>
      <span class:online={health === 'ok'}>Server: {health}</span>
    </div>
    <nav class="toolbarActions" aria-label="Project actions">
      <button type="button" onclick={openDiagram}>Open</button>
      <button type="button" onclick={saveActiveDiagram}>Save</button>
      <button type="button" onclick={addSchematicTab}>New schematic</button>
      <button type="button">Generate script</button>
      <button type="button">Run simulation</button>
    </nav>
  </header>

  <div class="workspaceShell">
    <aside class="leftSidebar" aria-label="Device palette">
      <div class="panelHeader">
        <h2>Device palette</h2>
        <span>{specs.length}</span>
      </div>

      {#if error}
        <section class="notice" role="alert">
          <strong>Message</strong>
          <p>{error}</p>
          <button type="button" onclick={loadShell}>Retry</button>
        </section>
      {:else if loading}
        <section class="empty">Loading specs...</section>
      {:else if specs.length === 0}
        <section class="empty">No generated specs found.</section>
      {:else}
        {#if notice}
          <section class="notice compact"><p>{notice}</p></section>
        {/if}
        <div class="paletteGroups">
          {#each groupedSpecs as [category, devices]}
            <section class="paletteGroup">
              <h3>{category}</h3>
              {#each devices as spec}
                <button
                  class:active={pendingSpec?.class_path === spec.class_path}
                  class="paletteDevice"
                  type="button"
                  onclick={() => selectPaletteDevice(spec)}
                >
                  <div>
                    <strong>{spec.gui_name || spec.class_path}</strong>
                    <small>{spec.icon || 'no icon'}</small>
                  </div>
                  <span>{Object.keys(spec.properties).length}</span>
                </button>
              {/each}
            </section>
          {/each}
        </div>
      {/if}
    </aside>

    <section class="centerPane" aria-label="Workspace">
      <div class="tabs" role="tablist" aria-label="Open editors">
        {#each tabs as tab}
          <button
            class:active={tab.id === activeTabId}
            type="button"
            role="tab"
            aria-selected={tab.id === activeTabId}
            onclick={() => {
              activeTabId = tab.id;
              selectedDeviceId = null;
            }}
          >
            {tab.title}
          </button>
        {/each}
      </div>

      <div class="editorArea">
        {#if activeTab?.kind === 'output'}
          <section class="outputEditor">
            <h2>Simulation Output</h2>
            <p>Validation, generated scripts, logs, and results appear here.</p>
            <button type="button" onclick={showOutputInBottomPanel}>
              Dock to bottom
            </button>
          </section>
        {:else if activeTab?.diagram}
          <SchematicEditorWrapper
            title={activeTab.title}
            diagram={activeTab.diagram}
            {specsByClassPath}
            {selectedDeviceId}
            {pendingSpec}
            onPlaceDevice={placeDevice}
            onSelectDevice={selectDevice}
          />
        {/if}
      </div>

      {#if outputMode === 'bottom'}
        <section class:collapsed={outputCollapsed} class="bottomPanel">
          <div class="bottomPanelHeader">
            <div>
              <strong>Simulation output</strong>
              <span>Validation, script generation, logs, results</span>
            </div>
            <div class="bottomPanelActions">
              <button
                type="button"
                onclick={() => (outputCollapsed = !outputCollapsed)}
              >
                {outputCollapsed ? 'Expand' : 'Collapse'}
              </button>
              <button type="button" onclick={showOutputAsTab}>
                Open as tab
              </button>
            </div>
          </div>
          {#if !outputCollapsed}
            <div class="outputContent">
              <p>No simulation output yet.</p>
            </div>
          {/if}
        </section>
      {:else if outputTabOpen}
        <button class="restoreOutput" type="button" onclick={showOutputInBottomPanel}>
          Restore output panel
        </button>
      {/if}
    </section>

    <aside class="rightSidebar" aria-label="Inspector">
      <div class="panelHeader">
        <h2>Inspector</h2>
      </div>

      {#if selectedDevice}
        <section class="specPreview">
          <h3>{selectedSpec?.gui_name || selectedDevice.type}</h3>
          <dl>
            <dt>Device id</dt>
            <dd>{selectedDevice.id}</dd>
            <dt>Type</dt>
            <dd>{selectedDevice.type}</dd>
            <dt>Icon</dt>
            <dd>{selectedSpec?.icon || 'none'}</dd>
          </dl>
          <h4>Properties</h4>
          {#if Object.keys(selectedDevice.properties).length === 0}
            <p class="muted">No properties</p>
          {:else}
            <ul class="propertyList">
              {#each Object.entries(selectedDevice.properties) as [name, value]}
                <li>
                  <span>{name}</span>
                  <small>{formatValue(value)}</small>
                </li>
              {/each}
            </ul>
          {/if}
        </section>
      {:else}
        <section class="inspectorPlaceholder">
          <strong>Selected item</strong>
          <p>No device, port, or connection selected.</p>
        </section>
      {/if}
    </aside>
  </div>
</main>
