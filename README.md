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
├── examples/              # Full working demos (e.g., BB84)
├── gui/                   # GUI assets and integration logic (optional)
├── tests/                 # Unit and integration tests
└── README.md              # You are here
```

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
