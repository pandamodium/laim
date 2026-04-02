"""Disk persistence for simulation runs.

Saves and loads simulation results (config + metrics) to disk so they
survive across Streamlit sessions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.config.parameters import SimulationConfig

# Default run storage directory (relative to project root)
DEFAULT_RUNS_DIR = Path("outputs/runs")


class RunStore:
    """Persist and recall simulation runs to/from disk."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or DEFAULT_RUNS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _run_dir(self, run_name: str, timestamp: str) -> Path:
        safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in run_name)
        return self.base_dir / f"{safe_name}_{timestamp}"

    def save(
        self,
        run_name: str,
        metrics_df: pd.DataFrame,
        config: SimulationConfig,
    ) -> Path:
        """Save a simulation run to disk.

        Args:
            run_name: Human-readable name for this run.
            metrics_df: Simulation metrics DataFrame.
            config: The SimulationConfig used.

        Returns:
            Path to the saved run directory.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = self._run_dir(run_name, ts)
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save metrics
        metrics_df.to_csv(run_dir / "metrics.csv", index=False)

        # Save config
        config_path = run_dir / "config.json"
        config_path.write_text(config.model_dump_json(indent=2))

        # Save summary metadata
        summary = {
            "run_name": run_name,
            "timestamp": ts,
            "num_periods": len(metrics_df),
            "created": datetime.now().isoformat(),
        }
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

        return run_dir

    def list_runs(self) -> List[Dict]:
        """List all saved runs.

        Returns:
            List of dicts with keys: name, timestamp, path, num_periods.
        """
        runs = []
        if not self.base_dir.exists():
            return runs

        for d in sorted(self.base_dir.iterdir(), reverse=True):
            if not d.is_dir():
                continue
            summary_path = d / "summary.json"
            if summary_path.exists():
                summary = json.loads(summary_path.read_text())
                runs.append({
                    "name": summary.get("run_name", d.name),
                    "timestamp": summary.get("timestamp", ""),
                    "created": summary.get("created", ""),
                    "num_periods": summary.get("num_periods", 0),
                    "path": d,
                })
        return runs

    def load(self, run_path: Path) -> Tuple[pd.DataFrame, SimulationConfig]:
        """Load a saved run from disk.

        Args:
            run_path: Path to the run directory.

        Returns:
            (metrics_df, config) tuple.
        """
        metrics_df = pd.read_csv(run_path / "metrics.csv")
        config_text = (run_path / "config.json").read_text()
        config = SimulationConfig.model_validate_json(config_text)
        return metrics_df, config

    def delete(self, run_path: Path) -> None:
        """Delete a saved run from disk.

        Args:
            run_path: Path to the run directory.
        """
        import shutil
        if run_path.exists() and run_path.is_dir():
            shutil.rmtree(run_path)
