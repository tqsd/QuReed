# Qureed: Quantum-Ready Simulation Framework

*QuReed* is a modular, backend-agnostic simulation framework for modeling quantum optical systems, photonic circuits, and hybrid quantum-classical workflows. It is designed to support intuitive device-based programing, enabling researchers and engineers to simulate, test, and analyze quantum processes in a schematic and flexible way.

## Features
- *Component-Based Simulation*: Build systems using devices like photon sources, detectors, beam splitters, waveplates, phase shifters, etc.
- *Hybrid Classical-Quantum Modeling*: Seamlessly integrate classical control logic with quantum operations.
- *Backend Support*: Built in support for `photon_weave` and skeleton for future backends like `qutip`.
- *Device Wrappers*: Easy definition of simulation behavior via `@des_proc` decorators for SimPy-based scheduling.

## Repository Structure
```bash
src/qureed/
├── devices/               # Built-in quantum/classical device models
├── simulation/            # Simulation orchestration and scheduling
├── signals/               # Signal types and propagation mechanics
├── backends/              # Backend-specific behavior (e.g., photon_weave)
├── interface/             # Project/spec/diagram/script/runtime services
├── cli/                   # Command-line interface
├── server/                # Optional FastAPI local server
└── gui/                   # Future packaged GUI assets

frontend/                  # Future frontend source, outside Python package
tests/                     # Unit and integration tests
```

Core simulation modules do not import the CLI, server, GUI, or interface
runtime layers. CLI and server code call the `qureed.interface.runtime`
service boundary, while device specs and diagrams remain JSON-facing for
future GUI code. GUI/server dependencies are optional and installed through
`qureed[gui]`; a normal `qureed` install remains lightweight.

## Frontend Development
The frontend source lives in `frontend/` and is not installed as part of the
Python package. It talks only to the local QuReed server API.

Install and run the frontend during GUI development:

```bash
cd frontend
npm install
npm run dev
```

Start the local server separately from a QuReed project:

```bash
qureed gui --project-root /path/to/project
qureed gui --project-root /path/to/project --open
```

The Vite dev server proxies `/health` and `/specs` to
`http://127.0.0.1:8000` by default. Set `VITE_QUREED_API_BASE` if the API is
served elsewhere.

Rebuild packaged frontend assets only when changing the frontend:

```bash
cd frontend
npm run build
```

The build output is written to `src/qureed/gui/static/` so installed GUI users
do not need Node.js at runtime.

## Installation
Install directly from GitHub repository (`simpy` branch):
```bash
pip install git+ssh://git@github.com/tqsd/QuReed.git@simpy
```

Or using HTTPS:
```bash
pip install git+https://github.com/tqsd/QuReed.git@simpy
```


## Documentation
- In-code docstrings and examples
- Full API reference (coming soon)
- Sphinx documentation build planned


## Roadmap
