<script lang="ts">
  import type { DeviceSpec, Diagram, DiagramDevice } from './types';

  export let title: string;
  export let diagram: Diagram;
  export let specsByClassPath: Map<string, DeviceSpec>;
  export let selectedDeviceId: string | null;
  export let pendingSpec: DeviceSpec | null;
  export let onPlaceDevice: (x: number, y: number) => void;
  export let onSelectDevice: (deviceId: string | null) => void;

  function handleSurfaceClick(event: MouseEvent) {
    if (!pendingSpec) {
      onSelectDevice(null);
      return;
    }

    const target = event.currentTarget as HTMLElement;
    const rect = target.getBoundingClientRect();
    onPlaceDevice(event.clientX - rect.left, event.clientY - rect.top);
  }

  function specFor(device: DiagramDevice): DeviceSpec | undefined {
    return specsByClassPath.get(device.type);
  }
</script>

<section class="schematicEditor" aria-label={`${title} schematic editor`}>
  <button
    class:placing={pendingSpec !== null}
    class="placementStatus"
    type="button"
  >
    {pendingSpec
      ? `Place ${pendingSpec.gui_name || pendingSpec.class_path}`
      : 'Select a device from the palette'}
  </button>

  <div
    class:placing={pendingSpec !== null}
    class="schematicSurface"
    role="button"
    tabindex="0"
    onclick={handleSurfaceClick}
  >
    {#if diagram.devices.length === 0}
      <div class="schematicPlaceholder">
        <h2>{title}</h2>
        <p>Click a palette device, then click here to place it.</p>
      </div>
    {/if}

    {#each diagram.devices as device}
      {@const spec = specFor(device)}
      <button
        class:selected={device.id === selectedDeviceId}
        class="deviceNode"
        style={`left: ${device.position.x}px; top: ${device.position.y}px;`}
        type="button"
        onclick={(event) => {
          event.stopPropagation();
          onSelectDevice(device.id);
        }}
      >
        <strong>{spec?.gui_name || device.type}</strong>
        <span>{spec?.icon || 'no icon'}</span>
      </button>
    {/each}
  </div>
</section>
