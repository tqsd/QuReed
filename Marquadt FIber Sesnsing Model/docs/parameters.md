# Editable parameters and provenance

Generated from the implemented component schemas. Units are explicit; frequency inputs are in Hz, optical powers in W, and lengths in m. Scientific notation is accepted in the GUI.

Source-confirmed values and ambiguities are detailed in [source-audit.md](source-audit.md). All numerical settings below that are not explicitly source-attributed are demonstration assumptions, not measured laboratory calibrations. Names and icon positions are UI metadata.

## Laser FM

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `frequency_hz` | 699000 | Hz | Nominal FM (delay/fixed control mode) | Paper operating rate; used directly only in delay/fixed mode. |
| `excursion_hz` | 47000000000 | Hz | Optical excursion (selected convention) | Reported bandwidth; total-span interpretation is provisional. |
| `excursion_convention` | peak-to-peak | dimensionless / selection | Excursion convention (peak-to-peak, peak) | Explicit interpretation supported by measured thesis spectrum; source equations inconsistent. |
| `group_velocity_m_s` | 204000000 | m/s | Fiber group velocity | Assumed group velocity, consistent with rounded reported spacing. |
| `delay_s` | 0.0000014306151645207439 | s | External pump minus probe delay | Derived demo delay 1/699000 s, not thesis geometry. |
| `correlation_order` | 1 | dimensionless / selection | Correlation order | Assumed demo order 1, not thesis order 84. |
| `phase_rad` | 0 | rad | Common modulation phase | Assumed phase; cancels in complete-period averages. |

## Shared CW laser

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `power_w` | 0.02 | W | Source optical power | Assumed demonstration setting. |
| `wavelength_nm` | 1550 | nm | Optical wavelength | Source wavelength near 1550 nm. |

## 50:50 splitter

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `pump_fraction` | 0.5 | dimensionless / selection | Pump power fraction | Supplied 50:50 apparatus. |
| `loss_db` | 0 | dB | Insertion loss | Assumed demonstration setting. |

## Probe RF sweep

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `frequency_start_hz` | 10600000000 | Hz | Offset sweep start | Source sweep interval. |
| `frequency_stop_hz` | 11100000000 | Hz | Offset sweep stop | Source sweep interval. |
| `frequency_step_hz` | 2000000 | Hz | Offset sweep step | Assumed 2 MHz sampling; convergence tested. |

## Probe EOM

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `eom_loss_db` | 20 | dB | Selected sideband effective loss | Assumed demonstration setting. |

## Probe PC

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `pc_overlap` | 1 | dimensionless / selection | SBS polarization overlap | Assumed demonstration setting. |

## Probe isolator

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `isolator_loss_db` | 0.5 | dB | Forward loss; ideal reverse blocking | Assumed demonstration setting. |

## Pump EOM

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `eom_loss_db` | 3 | dB | Mean insertion loss | Assumed demonstration setting. |
| `modulation_depth` | 0.2 | dimensionless / selection | Intensity AM depth (linear model) | Assumed demonstration setting. |

## Pump EDFA

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `edfa_gain_db` | 13 | dB | Power gain | Assumed demonstration setting. |
| `edfa_max_w` | 0.2 | W | Maximum output power | Assumed demonstration setting. |

## Circulator

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `circulator_loss_db` | 0.5 | dB | Loss for each routed pass | Assumed demonstration setting. |

## Fiber 4 (all four segments)

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `length_m` | 0.1 | m | Physical segment length | User-approved toy geometry, not paper fiber. |
| `resonance_hz` | 10850000000 | Hz | Local Brillouin resonance | Assumed 10.85 GHz; Fiber 3 is 10.90 GHz. |
| `linewidth_hz` | 27000000 | Hz | Intrinsic gain FWHM | Source intrinsic gain FWHM. |
| `gain_per_w_m` | 0.5 | 1/(W m) | Effective SBS gain coefficient | Assumed demonstration setting. |
| `attenuation_db_km` | 0.2 | dB/km | Power attenuation | Assumed demonstration setting. |

## Pump output

No editable physical parameters; this block terminates the pump route.

## Pump AM + ref

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `modulation_hz` | 100000 | Hz | Pump tag frequency | Thesis confirmed 100 kHz intensity tag. |
| `phase_deg` | 0 | deg | Pump tag phase | Assumed demonstration setting. |

## Probe detector

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `responsivity_a_w` | 0.9 | A/W | Responsivity | Assumed demonstration setting. |
| `transimpedance_v_a` | 10000 | V/A | Transimpedance | Assumed demonstration setting. |
| `bandwidth_hz` | 1100000 | Hz | Single-pole detector bandwidth | Assumed demonstration setting. |
| `max_voltage_v` | 10 | V | Voltage limit | Assumed demonstration setting. |

## Lock-in X / Y

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `reference_phase_deg` | 0 | deg | Reference phase | Assumed demonstration setting. |
| `time_constant_s` | 0.001 | s | RC time constant | Assumed demonstration setting. |
| `filter_order` | 1 | dimensionless / selection | Cascaded RC stages | Assumed demonstration setting. |
| `dwell_s` | 0.01 | s | Dwell per spectral point | Assumed demonstration setting. |

## Position scan

| Parameter | Default | Unit | Meaning | Provenance |
|---|---:|---|---|---|
| `target_m` | 0.25 | m | Local target position | Assumed demonstration setting. |
| `start_m` | 0.025 | m | Spatial scan start | Assumed demonstration setting. |
| `stop_m` | 0.375 | m | Spatial scan stop | Assumed demonstration setting. |
| `step_m` | 0.01 | m | Spatial scan step | Assumed demonstration setting. |
| `cell_m` | 0.002 | m | Numerical cell size (not resolution) | Numerical quadrature choice, not sensing resolution. |
| `position_control` | frequency | dimensionless / selection | Position control (frequency, delay, fixed) | Assumed demonstration setting. |
| `background_subtraction` | false | dimensionless / selection | Background subtraction (unsupported) | Off by design; true is rejected, not silently ignored. |

## Coupled settings and limits

Changing lengths updates segment coordinates and the physical delay-to-position map. Keep requested scan positions inside the new total length. Fiber material order is inferred from connections, not the order of devices in JSON.

In frequency position-control mode, actual FM is solved from target/delay/order and shown in results. In delay mode, FM is held fixed and delay is solved. Fixed mode cannot execute a spatial scan. A common phase cancels from period averages.

The optical budget in the default model gives 89.125 mW pump entering the fiber, 89.125 microW probe entering the opposite end, and 79.431 microW at the detector before SBS. These are calculated assumed powers, not measured powers. The EDFA ceiling applies to peak tagged power, not just mean power.

The peak-to-peak interpretation gives about 4.62 cm local-response FWHM at the reference linewidth; changed line shape, linewidth, overlapping peaks or boundary mixing may give a different effective measurement width.
