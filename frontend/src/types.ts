export type HealthResponse = {
  status: string;
};

export type ProjectSummary = {
  name: string;
  root: string;
};

export type DeviceProperty = {
  type?: string;
  default?: unknown;
  value?: unknown;
  [key: string]: unknown;
};

export type DeviceSpec = {
  id: string;
  class_path: string;
  source: string;
  category: string;
  gui_name: string;
  icon: string | null;
  properties: Record<string, DeviceProperty>;
  path: string;
  valid: boolean;
};

export type WorkspaceTab = {
  id: string;
  title: string;
  kind: 'schematic' | 'output';
  path?: string;
  diagram?: Diagram;
};

export type OutputDockMode = 'bottom' | 'tab';

export type DiagramPosition = {
  x: number;
  y: number;
};

export type DiagramDevice = {
  id: string;
  type: string;
  position: DiagramPosition;
  properties: Record<string, unknown>;
};

export type DiagramConnection = {
  id?: string;
  source: {
    device: string;
    port: string;
  };
  target: {
    device: string;
    port: string;
  };
};

export type Diagram = {
  version: number;
  devices: DiagramDevice[];
  connections: DiagramConnection[];
};

export type DiagramResponse = {
  path: string;
  diagram: Diagram;
};
