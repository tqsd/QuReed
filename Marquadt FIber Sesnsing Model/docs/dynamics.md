# Coupled transient SBS envelope model

Status: NUMERICAL / independently checked in bounded regimes. Date:2026-09-05. This is the time-dependent optical/acoustic extension, separate from the cycle-averaged Floquet spectrum. It actually propagates both counterpropagating optical fields and evolves an acoustic field with finite lifetime. It is not a stationary power boundary-value problem relabelled as transient.

## State and equations

The pump enters at $z=0$ and the probe at $z=L$. Pump and probe complex amplitudes $p,s$ have units $\sqrt{\mathrm W}$. Removing their known retarded common-laser FM phases leaves slowly varying envelopes. The transformed acoustic amplitude $q$ is normalized in W so its steady resonant value is $ps^*$. Its magnitude is not a thermodynamic acoustic energy.

The actual equations are

$$
(\partial_t+v_g\partial_z)p=-{v_gg r\over2}qs-{v_g\alpha\over2}p,
$$
$$
(\partial_t-v_g\partial_z)s=+{v_gg\over2}q^*p-{v_g\alpha\over2}s,
$$
$$
\partial_tq=\gamma ps^*-[\gamma+i2\pi\delta(z,t)]q.
$$

Here $g$ includes the configured effective gain and polarization overlap, $\alpha$ is the power attenuation coefficient, $\gamma=\pi\Gamma_B$, and $r=\nu_p/\nu_s$. The configured laser wavelength identifies nominal pump carrier $\nu_p=c/\lambda$; $\nu_s=\nu_p-\nu_{offset}$. The tiny time variation of this ratio under optical FM is neglected, while FM detuning itself is retained exactly:

$$
\delta(z,t)=\nu_{offset}-\nu_B(z)
+D\{\sin[2\pi f_m(t-\tau_p)+\phi_0]-\sin[2\pi f_m(t-\tau_s)+\phi_0]\}.
$$

The source delays use the same coordinate convention as the baseline model. Thus optical propagation, local acoustic memory, and stimulated energy transfer are coupled, and probe amplification changes pump power during the run.

Initially the optical fields are zero. Both boundary intensities rise exponentially with the editable turn-on time. The pump additionally carries the configured sinusoidal intensity tag. An optional acoustic seed can be supplied; default zero gives deterministic stimulated dynamics. There is no spontaneous Langevin field in this solver.

## Conservation and numerical method

Local SBS coupling conserves the photon-weighted optical power $|p|^2/r+|s|^2$. The optical **energy** powers do not sum exactly when pump and probe frequencies differ; the difference corresponds to acoustic energy transfer. The chosen acoustic normalization does not support a separate absolute phonon energy claim.

The uniform finite-volume grid has $\Delta t=\Delta z/v_g$. Optical advection is an exact one-cell characteristic shift: pump right, probe left. The acoustic state stays at its material cell. Strang splitting applies half local evolution, the optical shift with boundary injection/extraction, and a second half local evolution. Local complex equations and attenuation loss are integrated with RK4.

For each shift the solver accumulates photon-weighted incoming and outgoing optical flux. Weighted storage is $(\Delta z/v_g)\sum_j(P_{p,j}/r+P_{s,j})$. RK4 quadrature separately integrates attenuation loss. The reported balance residual is

$$
{E_{stored}+E_{out}+E_{loss}-E_{in}\over E_{in}}.
$$

This is an independent accounting residual; loss is not defined afterward to make conservation hold. A residual exceeding$10^{-3}$ raises an error. Step guards also require bounded acoustic detuning and coupling advance per time step. Grid/step refinement is still needed even if conservation is excellent.

The reported `pump_depletion_fraction_final` compares pump output to the **retarded no-SBS output with the same turn-on, tag, and attenuation**. The separate `pump_total_transmission_deficit_final` also includes ordinary loss/turn-on/tag timing. Probe amplification likewise divides by the retarded, attenuated no-SBS probe output; its simultaneous-boundary transmission ratio is exported separately. Depletion/amplification are null before the corresponding reference field arrives or when its input is zero. This prevents normal propagation delay or fiber loss from being misidentified as SBS depletion/gain.

## Demonstration and convergence

Default options use40 cells,150ns, pump multiplier1, probe multiplier50, and coupling multiplier100. The latter two are explicit demonstration choices that make depletion visible; they are not paper values. The default frequency offset is10.90GHz and common FM is enabled. With the four-segment baseline the initial numerical run shows approximately2% pump depletion and probe amplification around1.50. Its simulated interval spans only about0.105 of a699kHz FM cycle. It does not claim a steady BOCDA spectrum or settled100kHz lock-in response.

`convergence_check=true` reruns the complete initial-boundary-value problem at twice the cell count and half the timestep, then compares interpolated boundary-output traces. The original150ns check gave relative L2 changes below0.1% for both output powers and photon-balance residual around$10^{-14}$. These values are numerical evidence for this parameter set, not universal error bounds.

Acceptance is explicit for each pump/probe output trace: RMS(coarse minus interpolated fine) must be at most `refinement_atol_w + refinement_rtol * RMS(fine)`. Defaults are 1 nW absolute and 1% relative. The absolute term defines behavior near zero signal. Exceeding either trace's tolerance raises a convergence error; the GUI does not label that run successful. Successful diagnostics record the errors, thresholds and `refinement_status=passed`. Disabling refinement records `not_checked` and a warning, not an implicit pass.

The result also records actual duration, the one-way propagation time $L/v_g$, acoustic amplitude lifetimes $1/(\pi\Gamma_B)$ across the segments, the number of propagation transits, and the minimum number of acoustic lifetimes simulated. These distinguish optical transit, acoustic relaxation and the separately reported FM-period count.

An independent referee also solved a stationary counterpropagating boundary-value problem for the no-FM/no-tag uniform lossless limit. With pump0.08912509W, probe0.00445625W, gain50/(Wm), and length0.4m, its predicted depletion was0.1893319 and probe amplification4.786425. The transient40-cell solution approached depletion0.1893501;80 cells gave0.1893374. The independent stationary benchmark is used only as a long-time limit check, not as the transient algorithm.

Output fields include time, position, pump/probe power maps, real/imaginary acoustic maps, boundary input/output traces, conservation histories, actual dt/dz, demonstration overrides, delay controls, and refinement diagnostics. Root-level exporters can plot these without rerunning the physics.

## Resource and modeling limits

The desktop solver limits the requested coarse grid to200 cells, time to2000ns, each run to250000 steps and40million cell-steps, and saved frames to501. Refinement doubles the grid internally. A long fiber with large optical-FM excursion may require a smaller time step than the configured grid supports and is rejected with a resolution message. Material boundaries are represented by the uniform cell-center material assignment; refinement is required when a segment boundary falls between grid boundaries.

The solver includes pump depletion and causal acoustic response but does not include EDFA population dynamics inside the spatial PDE, spontaneous Brillouin noise, independent polarization vectors, acoustic propagation between cells, dispersion, or reflection. The nonideal spectrum module handles its own explicitly averaged component/noise models; combining every optional effect into one full stochastic PDE is not claimed. Optical carrier cycles near193THz are analytically removed, not numerically sampled.

Tests check zero-coupling propagation and conservation, actual strong-probe depletion, comparison with the independent stationary benchmark, grid/time refinement, nonzero dynamic acoustic phase under common FM, and preflight resource/rate errors. Conclusions remain bounded numerical validation.
