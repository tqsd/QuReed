
# BB84 Quantum Key Distribution Example (QuReed)

This example implements a basic simulation of the **BB84 Quantum Key Distribution (QKD)** protocol using the [QuReed](https://github.com/) simulation framework.

The BB84 protocol enables two parties — commonly referred to as **Alice** and **Bob** — to securely establish a shared cryptographic key using quantum optics.

---

## What This Example Does

- Simulates a full BB84 setup using polarization-encoded photons
- Includes both the sender (Alice) and receiver (Bob)
- Emulates random bit and basis generation, state preparation, measurement, and classical post-processing
- Performs **basis reconciliation** and **key confirmation**
- Verifies the correctness of the shared quantum key at the end

---

## Structure
```bash
examples/bb84/
├── random_basis_trigger.py # Alice's random bit & basis generator
├── random_basis_detection.py # Bob's random basis selection & measurement
├── basis_confirmation_signal.py # Shared signal class for basis reconciliation
├── main.py # Simulation setup and execution (BB84 function)
```


## How to Run

1. Ensure you have `qureed` and `photon_weave` installed.
2. Run the main simulation script

```bash
python main.py
```

You should see output similar to:
```bash
Quantum Key Check
----------------------
Alice's key: [1, 0, 1, 0, 1, 1]
Bob's key:   [1, 0, 1, 0, 1, 1]
Key length:  6
Mismatches:  0
Accuracy:    100.00%
```

## Devices Used
|----------------------|------------------------------------|
| Device               | Role                               |
|----------------------|------------------------------------|
| RandomBasisTrigger   | Alice's bit/basis generator        |
| IdealNPhotonSource   | Single-photon emitter              |
| IdealTunableWaveplate| Applies polarization rotations     |
| RandomBasisDetection | Bob's basis selection and detector |
| ConstantClock        | Drives time in simulation          |
|----------------------|------------------------------------|
