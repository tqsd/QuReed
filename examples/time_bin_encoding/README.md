# Time-Bin Encoding Example

This example implements a simulation of *time-bin encoded quantum states*.

*Time-bin encoding* is a method for encoding quantum information in the arrival times (early/late or multiple time bins) of single photons.

## What This Example Does
- Simulates a basic time-bin encoding and measurement setup
- Generates single photons in three time bins
- Uses a Mach-Zehnder interferometer (MZI) network to create and manipulate time-bin qubits
- Moduls realistic delays, phase shifts, and beam splitters
- Performs time-resolved detection at the output, collecting statistics on photon  arrival in each time bin and detector.
- Visualizes detection probabilities as a bar plot for each pulse and detector channel.

## Structure
```bash

examples/time_bin_encoding/
├── custom_tbe_measurement.py # Time-bin resolved detector logic & statistics
├── main.py # Experiment setup and execution (time_bin_encoding function)
```

## How to run
1. Ensure you have `qureed` and `photon_weave` installed.
2. Run the main simulation script

```bash
python main.py
```
