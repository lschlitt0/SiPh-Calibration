# SiPh-Calibration

Research simulations of partitioned calibration for a coupled tuner mesh and
feedback relocking of a thermally coupled ring bank. Each module-level function
has its own file in `calibration_functions/`. `Calibration.py` is the CLI
entry point and re-exports the existing interfaces. The device models are
synthetic models, not measured silicon-photonic devices or instrument drivers.

Associated paper: [Scalable Design-for-Calibration of Programmable Silicon Photonics](https://doi.org/10.1109/ETS69887.2026.11591868),
IEEE European Test Symposium (ETS), 2026. See [Citation](#citation) for the full
reference and BibTeX.

## Overview

The mesh experiment compares partitioned surrogate calibration (`dfc`), one global
surrogate (`global`), and finite-difference coordinate updates (`tunecheck`). The
ring experiment compares simultaneous dither/lock-in feedback (`parallel`) with
the existing sequential scan-and-retune baseline (`scan`). Results include
calibration residuals, probe counts, hardware-write accounting, and ring detuning
metrics. Reported hardware writes are simulated events.

## Motivation

Coupled tuning controls can make calibration expensive because changing one
control affects several measured responses. The mesh model represents these
dependencies with weighted hyperedges and tests local surrogate fitting followed
by boundary correction. The ring model represents a temperature disturbance,
first-order thermal response, and decaying cross-talk between actuators. These
models support algorithm exploration; they do not establish device-level optical
accuracy, tuning power, or experimental performance.

## Repository Contents

| File | Purpose |
|---|---|
| [Calibration.py](Calibration.py) | CLI entry point and imports for the calibration interfaces |
| [calibration_functions/](calibration_functions/) | One module-level function per file, named after that function |
| [calibration_functions/models.py](calibration_functions/models.py) | Configuration dataclasses, synthetic plant/surrogate classes, counters, and controller classes |
| [calibration_functions/settings.py](calibration_functions/settings.py) | Import-time output paths and verbosity settings |
| [calibration_functions/constants.py](calibration_functions/constants.py) | Export field definitions and shared constant mappings |
| `test_calibration.py` | Test runner that registers the seven calibration tests; no embedded test bodies |
| `test_function_layout.py` | Compatibility runner that registers the four layout/import tests; no embedded test bodies |
| [calibration_test_functions/](calibration_test_functions/) | One existing test function per same-named file, plus shared loading/path settings in `_support.py` |
| `examples/example_usage.py` | Small seeded mesh and ring example using the existing function interfaces |
| `requirements.txt` | Required third-party package for the numerical workflows |
| `results/README.md` | Output locations, overwrite behavior, and generated artifacts |
| `LICENSE` | License status; an owner decision is required before selecting a license |

## Function Index

The table provides starting points for common changes. Each module-level
calibration function, including private helpers, lives in `calibration_functions/<name>.py`.
Nested functions remain with the function that owns their closure; class methods
remain with their classes in `models.py`.

Test bodies follow the same one-function-per-file layout in
`calibration_test_functions/`. The two root test modules bind those functions
onto `unittest.TestCase` classes, preserving individual test method names
and test discovery. They contain no function definitions. For example,
`test_tunecheck_probe_invariant` lives in
[its own file](calibration_test_functions/test_tunecheck_probe_invariant.py).

| Area | Implementation files |
|---|---|
| CLI and experiment profiles | [main](calibration_functions/main.py), [build_arg_parser](calibration_functions/build_arg_parser.py), [paper_profile](calibration_functions/paper_profile.py), [apply_paper_profile](calibration_functions/apply_paper_profile.py) |
| Synthetic mesh generation | [build_toy_mesh_hypergraph](calibration_functions/build_toy_mesh_hypergraph.py), [build_toy_mesh_plant](calibration_functions/build_toy_mesh_plant.py) |
| Partitioning | [partition_hypergraph](calibration_functions/partition_hypergraph.py), [balanced_kway_hypergraph_partition](calibration_functions/balanced_kway_hypergraph_partition.py) |
| Surrogate fitting and optimization | [fit_surrogate_with_trust_region](calibration_functions/fit_surrogate_with_trust_region.py), [gauss_newton_solve](calibration_functions/gauss_newton_solve.py) |
| Mesh calibration and baselines | [run_dfc_mesh](calibration_functions/run_dfc_mesh.py), [run_mesh_global_surrogate](calibration_functions/run_mesh_global_surrogate.py), [run_mesh_tune_and_check](calibration_functions/run_mesh_tune_and_check.py), [run_mesh_suite](calibration_functions/run_mesh_suite.py) |
| Ring controllers and metrics | [simulate_ring_bank](calibration_functions/simulate_ring_bank.py), [simulate_ring_scan](calibration_functions/simulate_ring_scan.py), [_ring_metrics_from_trace](calibration_functions/_ring_metrics_from_trace.py), [run_ring_suite](calibration_functions/run_ring_suite.py) |
| Sweeps | [expand_sweep_spec](calibration_functions/expand_sweep_spec.py), [apply_sweep_overrides](calibration_functions/apply_sweep_overrides.py) |
| Figures | [generate_hypergraph_plots](calibration_functions/generate_hypergraph_plots.py), [generate_mesh_plots](calibration_functions/generate_mesh_plots.py), [generate_ring_plots](calibration_functions/generate_ring_plots.py) |
| Paper exports | [write_paper_mesh_table](calibration_functions/write_paper_mesh_table.py), [write_paper_ring_table](calibration_functions/write_paper_ring_table.py), [write_paper_manifest](calibration_functions/write_paper_manifest.py) |

Use `from Calibration import run_dfc_mesh` to import from the main entry point.
For direct access to an implementation, use
`from calibration_functions.run_dfc_mesh import run_dfc_mesh`; import classes
from `calibration_functions.models`. The package `__init__.py` does not re-export
functions.

Private monkeypatches must target the module where a name is looked up. For
example, replacing a helper imported by `run_dfc_mesh` requires patching that
name in `calibration_functions.run_dfc_mesh`, rather than in `Calibration`.
Assignments to re-exported settings in the entry-point module do not propagate
to the implementation modules. Set `CAL_RESULTS_DIR` and `CAL_VERBOSE` before
importing the code or starting the CLI to configure their import-time defaults.

## Requirements

Tested with Python 3.14.4 and NumPy 2.4.4/2.5.3. No supported Python version range
was declared in the source; compatibility with other versions has not been
established.

**Required:** `numpy`, including `numpy.typing`. The standard-library modules
provide the CLI, serialization, path handling, timing, and tests. No SciPy,
pandas, machine-learning, or hardware-control library is imported.

**Optional, based on imports in `calibration_functions/`:**

| Dependency | Used for | Behavior without it |
|---|---|---|
| `matplotlib` | PNG plots | Plot generation is skipped with a message |
| `openpyxl` **or** `xlsxwriter` | `results.xlsx` summaries and traces | Workbook is skipped; `openpyxl` is preferred if both exist |
| `mtkahypar` **or** `kahypar` | External hypergraph partitioning | `auto` falls back to the built-in heuristic; explicit `kahypar` selection fails if unavailable |
| `docplex` and a working CPLEX solver backend | Constrained quadratic steps | `auto` can fall back to NumPy steps; explicit `docplex` selection requires a functioning backend |

The partition adapter first tries `mtkahypar`, then `kahypar`. The latter requires
an existing INI file via `--kahypar-config`; none is supplied in this repository.
The plotting adapter also reads `KAHYPAR_CONFIG`, but the mesh calibration adapter
does not, so use the CLI option for consistent partition selection. CPLEX is a
backend requirement of the `docplex` solve path, not a
direct import in this code. Solver installation, runtime availability, and any
licensing are separate from installing the required NumPy dependency.

## Installation

Run these commands from the repository directory:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
$env:PYTHONUTF8 = "1"
```

Windows Command Prompt:

```bat
.venv\Scripts\activate.bat
set PYTHONUTF8=1
```

The Windows UTF-8 setting supports the runner's mathematical symbols when output
is redirected to a file or pipe. Without it, a legacy console encoding can raise
`UnicodeEncodeError`, including for `--help`. Set it in each new shell session.

Linux/macOS:

```bash
source .venv/bin/activate
```

Then install the required package:

```bash
python -m pip install -r requirements.txt
```

To also produce the runner's figures and workbook:

```bash
python -m pip install matplotlib openpyxl
```

The built-in `heuristic` partitioner and `gn` optimizer need no external solver.

## Running the Code

The main entry point is `Calibration.py`. A small run of all calibration methods
with explicitly selected built-in solvers is:

```bash
python Calibration.py --mesh-size 4 --partitions 2 --rings 4 --ring-cross-talk-sweep=0.06 --partition-solver heuristic --opt-solver gn --results-dir results/small_run
```

The unchanged full default experiment is:

```bash
python Calibration.py
```

That default uses a 16-by-16 mesh, four partitions, eight rings, all three mesh
methods, both ring methods, seed 7, and cross-talk levels
`0,0.03,0.06,0.10,0.15`. Its `auto` solver choices depend on installed packages.
The global-surrogate case can be substantially more expensive than the small
example. For a fixed built-in configuration and table/manifest exports, use:

```bash
python Calibration.py --paper-profile --results-dir results/paper_profile
```

`--paper-profile` calls `apply_paper_profile()` and overrides the experiment
settings, including seed, sizes, methods, solvers, and sweeps. It preserves the
chosen output directory.

Use `python Calibration.py --help` for CLI options, `--no-rings` for mesh-only
runs, or `--no-mesh` for ring-only runs. No measurement files are required.

## Calibration Workflow

**Mesh (`run_dfc_mesh`).**

1. `build_toy_mesh_hypergraph()` constructs weighted 2-by-2 patch and L-shaped
   couplings on an N-by-N tuner grid. `build_toy_mesh_plant()` creates seeded
   linear/quadratic residual maps and hidden nominal controls. Applied controls
   start at zero.
2. Partition tuners to reduce weighted hyperedge connectivity cuts, with an
   upper block-weight balance constraint. The heuristic reports the balance
   check; it does not guarantee feasibility for every input.
3. Probe each block with bounded sign patterns. `ToyMeshPlant.measure()` maps
   controls to noisy scalar residuals, one per hyperedge. Fit a local ridge
   surrogate to internal-edge residuals; assess a held-out subset, adapt the
   trust radius/model, and check Jacobian conditioning.
4. `gauss_newton_solve()` seeks zero surrogate residual using damped updates with
   bounds, per-step slew limits, and a trust region. Block solutions are applied
   together in the simulated accounting; the Python computations run sequentially.
5. Repeat block fitting/optimization up to `outer_rounds`, stopping that loop if
   the noiseless global MSE is at or below `target_mse`. Then run the configured
   boundary-only polishing rounds on cut-edge residuals.
6. Return a dictionary of residual histories, block diagnostics, solver metadata,
   and effort. A returned result is not a guarantee that the target was reached.

`run_mesh_global_surrogate()` uses the same pipeline with one partition and no
boundary polishing. `run_mesh_tune_and_check()` probes a random tuner subset with
two measurements (positive and negative perturbations) per tuner and applies
clipped coordinate updates from the central difference. Its
round loop also checks the global MSE threshold.

**Rings (`simulate_ring_bank`).** A seeded initial detuning and fixed temperature
step drive a first-order thermal model. Normalized actuator commands and
exponentially decaying cross-talk determine target detuning. Sinusoidal dither
modulates each command; the readout is a synthetic squared-detuning signal plus
noise. Phase-compensated lock-in demodulation produces an estimated signed error.
`IncrementalPID.step()` updates commands with slew and amplitude limits. With the
implemented gains, only the integral term is nonzero. Simulation always runs the
five-second horizon, and settling is assessed afterward. The function also runs
a zero-cross-talk reference using the same noise seed.

`simulate_ring_scan()` instead reads noisy detuning directly and updates one active
ring at a time, moving to the next only after a dwell criterion. Its retained
update decreases the command for positive detuning; with the negative plant gain,
this increases the target detuning. The two methods also use different readout
models, which should be considered when interpreting their comparison.

## Example

```bash
python examples/example_usage.py
```

The example calibrates 16 normalized mesh controls in two partitions and simulates
four rings with seed 7, using NumPy alone. It prints initial/final mesh MSE, target
attainment, probe/write/iteration counts, and ring settling/peak/RMS metrics.
It does not create plots, tables, or a workbook. A minimal existing-API call is:

```python
from Calibration import CalibrationConfig, PhysicsParams, run_dfc_mesh

cfg = CalibrationConfig(
    mesh_size=4, partitions=2, seed=7,
    partition_solver="heuristic", opt_solver="gn",
)
result = run_dfc_mesh(cfg, PhysicsParams())
print(result["mse_final"], result["probe_count"], result["hw_write_count"])
```

With Python 3.14.4 and NumPy 2.4.4, the example
produced mesh MSE `0.1848795715 -> 0.0010434052`, 240 probes, 176 effective probe
rounds, six hardware writes, and 49 solver iterations. The MSE improved but did
**not** reach the configured `1e-4` threshold. The four rings met the filtered
settling criterion at 2887 ms, with peak error 6.96091 pm, final filtered RMS
0.0180633 pm, and 20,000 readouts. Use tolerances for floating-point comparisons;
host execution times vary.

## Using This Code in Your Research

- **Experiment sizes and coupling:** set `CalibrationConfig.mesh_size`,
  `partitions`, `ring_count`, `ring_cross_talk`, and `drift_K`, or their CLI
  equivalents. Configuration fields are listed directly in the dataclass.
- **Device model:** mesh topology and synthetic coefficients are defined by
  `build_toy_mesh_hypergraph()`, `build_toy_mesh_plant()`, and
  `ToyMeshPlant.measure()`. Ring state equations and constants are local to
  `simulate_ring_bank()` and `simulate_ring_scan()`. Substituting measured models
  requires deliberate edits at those points; there is no device-injection API.
- **Physical parameters:** `PhysicsParams` contains wavelength, index, lengths,
  thermo-optic coefficient, and responsivity fields. In these implementations,
  selected fields are exported as metadata only. Changing them does **not**
  change either simulated plant's state equations.
- **Initial conditions:** mesh commands start at zero; the hidden reference state
  and coefficients are seeded in the plant builder. Ring commands start at zero,
  and initial detuning scales with `drift_K` and a seeded per-ring variation.
  There is no CLI option for an arbitrary initial state.
- **Targets:** the mesh targets a zero residual vector; `target_mse` is its outer
  stopping threshold, set through the dataclass (no corresponding CLI flag).
  Ring locking targets zero detuning. Different set points require editing the
  relevant residual/state definition; no wavelength or phase-target API exists.
- **Controllers and optimizers:** expose existing configuration fields for round
  counts, solver selection, balance, and tune-and-check settings. Local surrogate
  constants and ring gains/rates/limits remain in their implementing functions;
  changing them constitutes a new experiment. `run_mesh_tune_and_check()` accepts
  `rounds`, `subset_frac`, `step_size`, and `lr` as keyword arguments; direct calls
  must pass these explicitly, whereas `run_mesh_suite()` maps the config fields.
- **Method comparisons:** CLI `--mesh-baselines dfc,global,tunecheck` and
  `--ring-baselines parallel,scan` select methods. The individual functions return
  dictionaries for custom analysis. The current mesh interfaces do not return
  the final control vector; do not infer device state from MSE alone.
- **Outputs:** choose `--results-dir` for each run; set `CAL_VERBOSE=0` to suppress
  ordinary progress messages (section/key metrics are still printed). Installed
  optional libraries enable plots and Excel exports automatically; there is no
  separate plotting-disable CLI flag.

A supported Cartesian sweep uses semicolons between configuration fields:

```bash
python Calibration.py --no-rings --partition-solver heuristic --opt-solver gn --sweep "N=4,6;k=2;seed=1..3" --results-dir results/mesh_sweep
```

Aliases include `N`, `k`, `rings`, `outer`, and `cross_talk`; configuration field
names are also accepted. Integer `a..b` ranges are inclusive. For ring coupling
studies, use `--ring-cross-talk-sweep=0,0.03,0.06`; the primary
`--ring-cross-talk` point is added if absent. Do not combine a custom sweep with
`--paper-profile`, which resets it. Keep partitions and device sizes physically
and numerically sensible; general input validation is limited.

## Important Parameters and Units

| Parameter | Meaning/default | Units | Where defined |
|---|---|---|---|
| `mesh_size`, `partitions` | N-by-N mesh, N=16; k=4 blocks | Counts | `CalibrationConfig` |
| `ring_count`, `ring_cross_talk` | 8 rings; off-diagonal coupling scale 0.06 | Count; dimensionless | `CalibrationConfig`, `_ring_cross_talk_matrix` |
| `balance_eps` | Maximum-block-weight slack, 0.05 | Dimensionless | `CalibrationConfig` |
| `outer_rounds`, `polishing_rounds` | Block passes and boundary passes, 2 each | Counts | `CalibrationConfig`, `run_dfc_mesh` |
| `target_mse` | Mesh outer-loop threshold, 1e-4 | Normalized residual squared | `CalibrationConfig` |
| `u_min`, `u_max`, mesh `max_slew` | Controls in [-1, 1]; per-solver-step change 0.05 | Normalized control; no voltage/power mapping | `ToyMeshPlant`, `run_dfc_mesh` |
| `noise_std` (mesh) | Probe noise standard deviation, 1e-3 | Normalized residual | `build_toy_mesh_plant` |
| `surrogate_lambda`, `target_val_mse` | Ridge regularization 1e-3; validation threshold 5e-3 | Code's normalized feature/residual convention | `run_dfc_mesh` |
| `initial_trust_radius`, `max_retries` | Initial probe radius 0.20; up to 4 fit attempts | Normalized control; count | `fit_surrogate_with_trust_region` |
| `gn_mu`, `gn_iters`, `cond_threshold` | Initial damping 1e-3; up to 20 steps; refit condition threshold 1e6 | Normalized solver convention; count; dimensionless | `run_dfc_mesh` |
| `tune_check_subset`, `tune_check_rounds`, `tune_check_step`, `tune_check_lr` | Defaults 0.3, 3, 0.05, 0.5 | Fraction; count; normalized control; normalized update gain | `CalibrationConfig`, `run_mesh_tune_and_check` |
| `drift_K`, `pm_per_K` | Temperature step 0.5; detuning coefficient 12 | K; pm/K | `CalibrationConfig`, both ring simulations |
| Ring `g`, `tau_s` | Detuning gain -25; thermal time constant 0.015 | pm/normalized control; s | Both ring simulations |
| `sample_rate_hz`, `sim_time_s` | Sampling 1000; horizon 5 | Hz; s | Both ring simulations |
| `pid_rate_hz`, `Kp`, `Ki`, `Kd` | Updates at 50 Hz; gains 0, 0.002, 0 | Hz; normalized control/pm per discrete update convention | `simulate_ring_bank`, `IncrementalPID.step` |
| Ring `u_min`, `u_max`, `du_max` | Commands in [-0.4, 0.4]; update limit 0.005 | Normalized control | `simulate_ring_bank` |
| `dither_base_hz`, `dither_step_hz`, `dither_amp_u` | 5 Hz plus 0.7 Hz per ring; amplitude 0.01 | Hz; normalized control | `simulate_ring_bank` |
| `lock_tau_s`, `lock_threshold_pm` | Demodulation filter 0.2; lock threshold 0.15 | s; pm | `simulate_ring_bank`; threshold also in scan |
| `seq_gain`, update clip, switching dwell | 0.02; 0.01; 0.15 s | Dimensionless; normalized control; s | `simulate_ring_scan` |
| `lam0_nm`, `n_eff`, `L_ps_um`, `L_ring_um` | 1550; 2.40; 200; 2*pi*10 | nm; dimensionless; um; um | `PhysicsParams` (metadata) |
| `dndT`, `pd_responsivity_A_per_W` | 1.8e-4; 0.9 | 1/K; A/W | `PhysicsParams` (metadata) |

There is no implemented heater power, voltage/current conversion, resonant
wavelength transfer function, or optical phase/transmission calculation. Ring
`p = d**2 + noise` is a synthetic error signal in pm squared, not optical power
in watts. The two ring methods both use a literal `noise_std=0.05` but add it to
different readouts (pm squared versus pm). `IncrementalPID` does not multiply or
divide gains by the sample period; the gains apply to its discrete recurrence.

## Methodology

The mesh partition objective is `sum_e weight_e * (lambda_e - 1)`, where
`lambda_e` is the number of blocks touched by an edge. A block surrogate uses an
intercept, linear terms, and selected pair products, fitted by regularized normal
equations. It is trained on noisy probes and checked on a randomized holdout.
The step solver minimizes local residuals with damped Gauss-Newton updates and
constraints. Mesh accuracy curves evaluate the synthetic plant with noise
temporarily disabled. Boundary polishing uses cut-edge residuals, so improvement
of a local objective need not improve the entire mesh.

The ring recurrence updates detuning toward
`drift_K * 12 + g * (u_drive + C @ u_drive)` using `dt/tau_s`. Dither frequencies,
thermal phase compensation, lock-in filtering, and the incremental controller
are implemented directly in `simulate_ring_bank()`. Neither case is a calibrated
electromagnetic or electrothermal device simulator.

## Reproducing Results

Use the example for a small reproducible function-level run, the explicit-solver
small-run command for end-to-end exports, or `--paper-profile` for the fixed
16-by-16/eight-ring experiment. All inputs are generated from configuration and
seed; there are no external source datasets. The profile uses seed 7, heuristic
partitioning, NumPy Gauss-Newton steps, and only cross-talk 0.06.

`random` and NumPy's legacy generator are seeded; local `default_rng` generators
use deterministic offsets for plant construction, probes, validation splits, and
ring noise. For example, mesh plant coefficients use `seed+101`, parallel-ring
initial conditions use `seed+17`, and its readout noise uses `seed+999`. Scan uses
different initial/noise seeds (`seed+71`, `seed+777`), so methods do not share all
random realizations. Seeds are already present and have not been changed.

Numerical results are seed-dependent and expected to reproduce within numerical
tolerance with fixed settings/environment. Different NumPy/BLAS builds, floating
point branching, external solver versions, and thread counts can affect results.
External partitioning uses `KAHYPAR_THREADS`/`MTKAHYPAR_THREADS` and
`KAHYPAR_PRESET`; the default can be multithreaded. Use explicit `heuristic`/`gn`
for comparisons that should not depend on optional solver discovery. Timings,
timestamps, output paths, and optional Git metadata are not deterministic.

The CLI writes to `results/` beside the script by default. `--results-dir`
overrides the main artifact directory. `CAL_RESULTS_DIR` sets the import-time
default root; secondary `--paper-profile` exports always go to that root's
`paper_data/` subdirectory, even when `--results-dir` selects another directory.
See [results/README.md](results/README.md) for file details and overwrite behavior.

Interpret the returned/exported metrics as follows:

| Metric | Interpretation |
|---|---|
| `initial_mse`, `mse_final`, `mse_curve` | Noiseless synthetic mesh residual mean square; normalized units |
| `probe_count` | Mesh probe evaluations or, for rings, ring readouts summed across every sample |
| `probe_rounds_effective` | Idealized parallel probe-round proxy; not measured hardware latency |
| `hw_write_count` | Simulated command commits under the method's counting convention |
| `hw_element_touch_count` | Number of individual controls touched by those commits |
| `solver_iter_count` | Counted solver/controller updates, distinct from hardware commits |
| `walltime` | Host execution time in seconds; not the ring simulation horizon |
| `settled_all`, `settle_ms` | Whether all filtered ring detunings met the threshold for a 0.25 s dwell, and the start of the first such window |
| `peak_pm` | Largest absolute raw detuning across rings and samples |
| `rms_pm` | RMS of low-pass-filtered detuning over the final second, across rings |

Ring settling/RMS metrics use an additional 0.25 s low-pass filter. A valid dwell
does not imply the rings stay locked for the rest of the run. If `settled_all` is
false, `settle_ms` equals the five-second horizon as a sentinel; it is not an
observed settling time. The paper table displays that case as `>5000` ms.

Check the existing invariants and extracted-module interfaces with:

```bash
python -m unittest discover -v
```

To run either suite separately, use `python -m unittest -v test_calibration`
or `python -m unittest -v test_function_layout`. Direct execution of those two
Python files also remains supported. Discovery runs each of the 11 tests once.

These tests check bookkeeping, exports, imports, and output paths; they do not
validate a physical device model.

## Citation

If you use this code in your research, cite the associated paper:

Lawrence Schlitt, Priyank Kalla, and Steve Blair, "Scalable Design-for-Calibration
of Programmable Silicon Photonics," in *2026 IEEE European Test Symposium (ETS)*,
Chania, Greece, 2026, pp. 1-6. DOI:
[10.1109/ETS69887.2026.11591868](https://doi.org/10.1109/ETS69887.2026.11591868).

[Published paper on IEEE Xplore](https://ieeexplore.ieee.org/document/11591868).

BibTeX:

```bibtex
@inproceedings{Schlitt2026SiPhCalibration,
  author    = {Schlitt, Lawrence and Kalla, Priyank and Blair, Steve},
  title     = {{Scalable Design-for-Calibration of Programmable Silicon Photonics}},
  booktitle = {2026 IEEE European Test Symposium (ETS)},
  year      = {2026},
  pages     = {1--6},
  address   = {Chania, Greece},
  publisher = {IEEE},
  doi       = {10.1109/ETS69887.2026.11591868},
  url       = {https://doi.org/10.1109/ETS69887.2026.11591868}
}
```

The title, authors, venue, year, and DOI were checked against the supplied
published PDF and IEEE's deposited [Crossref metadata](https://api.crossref.org/works/10.1109/ETS69887.2026.11591868).
The page range and conference location are recorded in that metadata. The DOI
identifies the paper; no separate software DOI or release version is assigned.

## License

See [LICENSE](LICENSE). No existing license was identified for the selected code;
the file records this unresolved owner decision and grants no license. Choose an
appropriate license after confirming the rights to distribute the code and any
institutional requirements.
