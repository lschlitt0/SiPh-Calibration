# Generated results

This directory is the default output location for `Calibration.py`. No external
measurement data are needed: both device models generate their inputs internally.
Generated results are excluded from version control; this file is retained.

The command-line runner writes:

- `terminal_output.txt`: captured console output, overwritten on each invocation
  using the same output directory.
- `table_mesh.tex`, `table_ring.tex`: summary tables for the cases that ran.
- `results.xlsx`: summary metrics and mesh/ring traces, when `openpyxl` or
  `xlsxwriter` is installed. An unavailable writer skips the workbook; the final
  console message can still name it, so check that the file exists.
- `fig_*.png`: plots when Matplotlib is installed; figures depend on which cases ran.
- `run_*` subdirectories: per-configuration tables and figures for multi-point
  parameter sweeps. The workbook and terminal log remain at the sweep output root.

With `--paper-profile`, the runner additionally writes
`paper_table_mesh.{tex,csv,json}`, `paper_table_ring.{tex,csv,json}`, and
`paper_manifest.json` to the selected output directory and to `paper_data/` under
the import-time default results directory. The manifest records configuration,
seed, requested/selected solvers, timestamp, paths, and a Git commit if available.
Its paths may identify the machine or account that generated it; review before sharing.

`--results-dir` chooses the main output directory. `CAL_RESULTS_DIR`, set **before
importing or starting the script**, chooses the default root and its `paper_data/`
subdirectory. With only `--results-dir` changed, the secondary paper exports still
go to the default `results/paper_data/`. Paths are defined in
[`calibration_functions/settings.py`](../calibration_functions/settings.py).
The default results directory remains `results/` at the repository root,
beside `Calibration.py`. Relative command-line/environment paths are
resolved against the working directory.

Use a fresh output directory for each experiment because exports overwrite files
of the same name. The example prints its summary to the terminal; it does not
generate a workbook, figures, or tables. Importing the main module creates the
default results directory even when no simulation is run. The CLI implementation
is in [`calibration_functions/main.py`](../calibration_functions/main.py); the
command is `python Calibration.py`.

See the repository [README](../README.md) for commands, model assumptions, and
metric definitions.
