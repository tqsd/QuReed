import type {
  DeviceSpec,
  Diagram,
  DiagramResponse,
  HealthResponse,
  ProjectSummary
} from './types';

const apiBase = import.meta.env.VITE_QUREED_API_BASE ?? '';

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

export async function fetchSpecs(): Promise<DeviceSpec[]> {
  return request<DeviceSpec[]>('/specs');
}

export async function fetchProject(): Promise<ProjectSummary> {
  return request<ProjectSummary>('/project');
}

export async function loadDiagram(path: string): Promise<DiagramResponse> {
  const query = new URLSearchParams({ path });
  return request<DiagramResponse>(`/diagrams/load?${query.toString()}`);
}

export async function saveDiagram(
  path: string,
  diagram: Diagram
): Promise<DiagramResponse> {
  return request<DiagramResponse>('/diagrams/save', {
    method: 'POST',
    body: JSON.stringify({ path, diagram })
  });
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers
    }
  });

  if (!response.ok) {
    const message = await readError(response);
    throw new Error(message);
  }

  return (await response.json()) as T;
}

async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === 'string') {
      return body.detail;
    }
  } catch {
    // Fall through to the HTTP status if the response is not JSON.
  }
  return `Request failed with ${response.status} ${response.statusText}`;
}
