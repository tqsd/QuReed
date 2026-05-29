# AGENTS.md

## Project Overview

QuReed is a modular simulation framework for quantum optical systems, photonic circuits, and hybrid quantum-classical workflows.

The existing QuReed core is the source of truth. Device implementation patterns must be preserved.

The current development goal is to add a lightweight interface layer around QuReed without changing the runtime device architecture.

---

## Critical Rule: Do Not Change the Core Device Model

Do not rewrite existing devices.

Do not change:

* existing device class inheritance
* `properties` dictionaries
* `Ports` usage
* `@des_proc` process methods
* SimPy coroutine behavior
* backend dispatch conventions such as `_attenuate_<backend>()`
* signal classes and signal type handling
* existing runtime execution semantics

The GUI and CLI layers must adapt to QuReed, not the other way around.

---

## Device Pattern

Existing devices may define metadata and runtime behavior directly on the class.

Typical structure:

```python
class SomeDevice(GenericDevice):
    properties = {
        "length": {"type": float, "value": 100},
    }

    @property
    def gui_name(self) -> str:
        return "Some Device"

    @des_proc
    def proc(self):
        ...
```

This pattern must remain valid.

---

## Development Strategy

Start with CLI tooling before building the web GUI.

Initial priority:

1. Inspect available devices
2. Generate static device specification files
3. Validate generated specs
4. Use specs as the source for future GUI rendering
5. Only then build the web frontend

The first implementation should not require constantly importing all devices during normal GUI runtime.

---

## Device Specification Files

Generate static device specs from existing QuReed devices.

The generated specs should describe:

* device class path
* display name
* category/module
* properties
* property types
* default values
* ports
* port directions
* accepted/emitted signal types if discoverable
* backend compatibility if discoverable
* documentation summary if available

Recommended output location:

```text
qureed_specs/devices/
```

Recommended format:

```text
qureed_specs/devices/lossy_fiber.json
```

Specs are generated artifacts. They should not replace the Python device classes.

---

## CLI First

Add CLI commands before the GUI.

Suggested commands:

```bash
qureed devices list
qureed devices inspect qureed.devices.fibers.lossy_fiber.LossyFiber
qureed specs generate
qureed specs validate
```

The CLI should be implemented in Python and should live outside the simulation core if possible.

Suggested package/module:

```text
qureed_cli/
```

or, if keeping the repo simpler:

```text
src/qureed/cli/
```

The CLI may import QuReed devices during spec generation. The future GUI server should prefer loading generated specs instead of importing every device at startup.

---

## Dependency Boundaries

The QuReed simulation core is the bottom layer. Core modules include:

```text
src/qureed/devices/
src/qureed/signals/
src/qureed/backends/
src/qureed/simulation/
src/qureed/errors/
src/qureed/logging/
src/qureed/utils/
```

Core modules must not import interface-layer modules:

```text
src/qureed/cli/
src/qureed/project/
src/qureed/registry/
src/qureed/specs/
src/qureed/diagram/
src/qureed/scriptgen/
src/qureed/runtime/
src/qureed/server/       # future
src/qureed/web/          # future
src/qureed/gui_server/   # future
```

Allowed dependency direction:

```text
future web frontend -> future server -> qureed/runtime
qureed/cli -> qureed/runtime
qureed/runtime -> qureed/project
qureed/runtime -> qureed/registry
qureed/runtime -> qureed/specs
qureed/runtime -> qureed/diagram
qureed/runtime -> qureed/scriptgen
qureed/registry -> qureed core
qureed/specs -> qureed core during generation only
qureed/diagram -> generated JSON specs
qureed/scriptgen -> diagrams + generated JSON specs
qureed core -> imports none of the interface/server/web layers
```

The runtime service is the stable boundary for future GUI/server code. CLI and future FastAPI handlers should call `src/qureed/runtime/service.py` where practical instead of reaching directly into lower-level helpers.

Generated device specs and diagram JSON are the GUI-safe data boundary. Future GUI/server startup should prefer reading generated JSON specs instead of importing every runtime device.

---

## Future Web GUI Architecture

The web GUI should be lightweight.

Suggested layers:

```text
qureed core
  existing simulation framework

qureed_cli
  inspection and spec generation tools

qureed_server
  FastAPI server for local GUI/runtime bridge

qureed_web
  Svelte + TypeScript + PixiJS frontend
```

Legacy architecture sketch:

```text
qureed_web -> qureed_server -> qureed/runtime -> qureed_specs / qureed
qureed_cli -> qureed/runtime
qureed core -> imports none of the GUI/server/CLI/runtime layers
```

Forbidden:

```text
qureed core -> qureed_server
qureed core -> qureed_web
qureed core -> qureed_cli
qureed core -> qureed/runtime
```

---

## GUI Philosophy

The GUI is a visual editor and launcher.

The frontend should not instantiate QuReed simulation objects.

The frontend edits a serializable project model.

The server converts that model into generated Python code or directly into QuReed runtime objects.

The first GUI version should support:

* loading device specs
* placing device nodes
* dragging nodes
* selecting nodes
* editing properties
* connecting compatible ports
* saving/loading project JSON

Simulation execution comes later.

---

## Project Model

The GUI project model should be plain JSON.

Example:

```json
{
  "devices": [
    {
      "id": "fiber_1",
      "type": "qureed.devices.fibers.lossy_fiber.LossyFiber",
      "position": {"x": 100, "y": 200},
      "properties": {
        "length": 100,
        "loss": 0.000046,
        "n": 1.45,
        "phaseShift": true
      }
    }
  ],
  "connections": []
}
```

---

## Implementation Rules

Prefer small, reviewable changes.

Each task should include tests when practical.

Do not introduce frontend code while implementing CLI/spec generation unless explicitly requested.

Do not introduce database/auth/collaboration features for the lightweight GUI.

Do not use Flet.

Use strict typing approach.

Use:

* FastAPI for the future local server
* Svelte + TypeScript for the future frontend
* PixiJS for the future diagram canvas
* Pydantic for API/spec schemas
* pytest for tests

---

## Current Milestone

The current goal is to prepare QuReed for a lightweight local web GUI while preserving the existing simulation core architecture.

The GUI must remain optional.

Installation targets:

```bash
pip install qureed
```

Installs:

* simulation core
* CLI tools
* device inspection
* spec generation utilities

without GUI runtime dependencies.

Optional GUI installation:

```bash
pip install "qureed[gui]"
```

Installs additional GUI-related dependencies such as:

* FastAPI
* uvicorn
* frontend static serving

The repository should remain a single unified project/repository.

Do not split QuReed into separate repositories or independent installable packages at this stage.

---

### Immediate Objectives

1. Refactor repository structure carefully without modifying the simulation core behavior.

2. Add internal modules for:

   * CLI utilities
   * spec generation
   * future GUI server

3. Implement CLI tooling for:

   * device inspection
   * device listing
   * static device spec generation
   * spec validation

4. Generate static JSON device specifications from existing devices.

5. Ensure the future GUI can load generated specs without importing all runtime devices continuously.

---

### Explicit Non-Goals For Current Milestone

Do NOT:

* rewrite existing devices
* redesign the runtime simulation architecture
* introduce database systems
* introduce authentication systems
* implement collaboration features
* implement cloud deployment
* tightly couple GUI and runtime logic
* implement full simulation execution in the GUI
* use Flet

---

### Current Internal Structure

Current structure:

```text
src/qureed/
  devices/       # simulation core
  simulation/    # simulation core
  signals/       # simulation core
  backends/      # simulation core

  project/       # qureed.toml loading and path resolution
  registry/      # device registry/discovery
  specs/         # static device spec generation/validation
  diagram/       # diagram JSON model/loading/validation
  scriptgen/     # diagram-to-script generation
  runtime/       # stable service facade for CLI/server/tests
  cli/           # command-line presentation layer
```

Future frontend source may live outside the Python package during development.

Built frontend assets may later be copied into the Python package for distribution.

---

### First CLI Targets

```bash
qureed devices list

qureed devices inspect \
  qureed.devices.fibers.lossy_fiber.LossyFiber

qureed specs generate

qureed specs validate
```

---

### Long-Term GUI Goal

The future GUI should be:

* lightweight
* browser-based
* local-first
* PixiJS-based
* backend-agnostic where practical

The frontend should consume generated device specifications and communicate with a lightweight local FastAPI server.
