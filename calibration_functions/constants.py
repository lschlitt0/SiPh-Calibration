"""Field names and sheet mappings for calibration result exports."""

from __future__ import annotations

MESH_ROW_FIELDS = (
    "timestamp",
    "seed",
    "method",
    "N",
    "k",
    "outer_rounds_run",
    "probe_count",
    "probe_rounds_effective",
    "hw_write_count",
    "hw_element_touch_count",
    "solver_iter_count",
    "mse_final",
    "mse_cut_edges_before_polish",
    "mse_cut_edges_after_polish",
    "mse_internal_edges_before_polish",
    "mse_internal_edges_after_polish",
    "walltime_s",
    "target_mse",
    "probes_per_tuner",
    "hw_writes_per_tuner",
    "hw_element_touches_per_tuner",
    "seconds_per_probe",
    "seconds_per_solver_iter",
    "partition_solver_requested",
    "partition_solver_used",
    "opt_solver_requested",
    "opt_solver_used",
    "subset_frac",
    "subset_size",
    "rounds_cfg",
    "step_size",
    "lr",
)


MESH_TRACE_FIELDS = (
    "stage",
    "block_id",
    "polish_round",
    "outer_round",
    "iter",
    "tuner_updates",
    "probes_total",
    "probe_rounds_effective",
    "probe_count",
    "hw_write_count",
    "solver_iter_count",
    "step_norm",
    "res_norm",
    "res_mse",
    "jacobian_cond",
    "mu",
    "global_mse",
    "walltime_s",
)


RING_ROW_FIELDS = (
    "timestamp",
    "seed",
    "method",
    "rings",
    "cross_talk",
    "probe_count",
    "probe_rounds_effective",
    "hw_write_count",
    "hw_element_touch_count",
    "solver_iter_count",
    "settled_all",
    "settle_step_all",
    "settle_ms",
    "peak_pm",
    "rms_pm",
    "walltime_s",
    "baseline_settle_ms",
    "drift_K",
    "controller_family",
    "lock_threshold_pm",
    "control_horizon_s",
    "dither_base_hz",
    "dither_step_hz",
    "pid_rate_hz",
    "Kp",
    "Ki",
    "Kd",
    "seq_gain",
    "update_clip",
    "switch_dwell_ms",
    "sim_time_s",
)


RUN_SUMMARY_FIELDS = (
    "timestamp",
    "seed",
    "run_walltime_s",
    "mesh_method",
    "mesh_mse_final",
    "mesh_probe_count",
    "mesh_probe_rounds_effective",
    "mesh_hw_write_count",
    "mesh_solver_iter_count",
    "mesh_walltime_s",
    "rings_method",
    "rings_settle_ms",
    "rings_peak_pm",
    "rings_rms_pm",
    "rings_probe_count",
    "rings_probe_rounds_effective",
    "rings_hw_write_count",
    "rings_solver_iter_count",
    "rings_walltime_s",
)


MESH_TRACE_SHEET_FIELDS = ("timestamp", "seed", "method", "N", "k") + MESH_TRACE_FIELDS


RING_TRACE_BASE_FIELDS = (
    "timestamp",
    "seed",
    "method",
    "cross_talk",
    "case",
    "t_ms",
)


RING_TRACE_SHEETS = {
    "ring_trace_detuning": "detuning_pm",
    "ring_trace_detuning_lp": "detuning_lp_pm",
    "ring_trace_u_cmd": "u_cmd",
    "ring_trace_e_hat": "e_hat",
}


PAPER_MESH_TABLE_FIELDS = (
    "Calibration strategy",
    "k",
    "Total probes",
    "Effective probe rounds",
    "HW writes",
    "Final MSE",
    "Time",
)


PAPER_RING_TABLE_FIELDS = (
    "Method",
    "Settle time (ms)",
    "Peak error (pm)",
    "RMS error (pm)",
)
