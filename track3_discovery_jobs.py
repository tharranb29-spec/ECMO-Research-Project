"""Bounded, file-backed shadow discovery jobs for the dashboard.

The default output directory survives browser refresh and process restart on the
same filesystem. Render's free ephemeral filesystem does not survive a new
instance; configure TRACK3_DISCOVERY_JOBS_PATH on persistent storage for that.
"""

import json
import os
import re
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path

import track3_discovery_workflow as workflow


ROOT = Path(__file__).resolve().parent
DEFAULT_JOBS_PATH = ROOT / "outputs" / "track3_discovery_jobs"
RUN_ID_PATTERN = re.compile(r"^shadow:[0-9a-f]{24}$")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class DiscoveryJobs:
    def __init__(self, path=None, runner=None, save_latest=None):
        self.path = Path(path or os.environ.get("TRACK3_DISCOVERY_JOBS_PATH", DEFAULT_JOBS_PATH))
        self.runner = runner or workflow.run_workflow
        self.save_latest = save_latest or workflow.save_state
        self.lock = threading.RLock()
        self.active_id = None
        self.path.mkdir(parents=True, exist_ok=True)
        self._mark_interrupted()

    def _file(self, run_id):
        if not RUN_ID_PATTERN.fullmatch(str(run_id)):
            raise ValueError("Invalid discovery run ID.")
        return self.path / f"{run_id.split(':', 1)[1]}.json"

    def _read(self, run_id):
        path = self._file(run_id)
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None

    def _write(self, job):
        path = self._file(job["run_id"])
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)

    def _mark_interrupted(self):
        for path in self.path.glob("*.json"):
            try:
                job = json.loads(path.read_text(encoding="utf-8"))
                if job.get("status") in {"queued", "running"}:
                    job.update(status="interrupted", stage="interrupted", updated_at_utc=utc_now(), error="Server restarted before this run completed; retry as a new run.")
                    self._write(job)
            except (OSError, ValueError, KeyError, TypeError):
                continue

    def submit(self, query, molecules, provider_mode):
        with self.lock:
            if self.active_id is not None:
                raise ValueError("A discovery run is already active; wait for it to finish or cancel it.")
            run_id = "shadow:" + secrets.token_hex(12)
            job = {
                "schema_version": 1,
                "run_id": run_id,
                "status": "queued",
                "stage": "queued",
                "created_at_utc": utc_now(),
                "updated_at_utc": utc_now(),
                "requested_mode": provider_mode,
                "query": query,
                "result": None,
                "error": None,
            }
            self._write(job)
            self.active_id = run_id
            threading.Thread(target=self._execute, args=(run_id, query, molecules, provider_mode), daemon=True, name=f"discovery-{run_id[-8:]}").start()
            return job

    def _progress(self, run_id, stage):
        with self.lock:
            job = self._read(run_id)
            if job and job["status"] != "cancelled":
                job.update(status="running", stage=stage, updated_at_utc=utc_now())
                self._write(job)

    def _execute(self, run_id, query, molecules, provider_mode):
        try:
            self._progress(run_id, "source_retrieval_and_extraction")
            result = self.runner(query, molecules=molecules, provider_mode=provider_mode, run_id=run_id, persist=False, progress=lambda stage: self._progress(run_id, stage))
            with self.lock:
                job = self._read(run_id)
                if job["status"] != "cancelled":
                    self.save_latest(result)
                    job.update(status="completed", stage="completed", result=result, updated_at_utc=utc_now())
                    self._write(job)
        except Exception as exc:  # noqa: BLE001 - bounded worker must record provider failures
            with self.lock:
                job = self._read(run_id)
                if job and job["status"] != "cancelled":
                    job.update(status="failed", stage="failed", error=str(exc)[:500], updated_at_utc=utc_now())
                    self._write(job)
        finally:
            with self.lock:
                self.active_id = None

    def get(self, run_id):
        with self.lock:
            return self._read(run_id)

    def latest(self):
        with self.lock:
            jobs = sorted(self.path.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
            for path in jobs:
                try:
                    return json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
            return None

    def cancel(self, run_id):
        with self.lock:
            job = self._read(run_id)
            if not job:
                raise ValueError("Discovery run not found.")
            if job["status"] not in {"queued", "running"}:
                raise ValueError("Only an active discovery run can be cancelled.")
            job.update(status="cancelled", stage="cancelled", updated_at_utc=utc_now(), error="Cancelled by reviewer; late provider output will be discarded.")
            self._write(job)
            return job

    def update_result(self, result):
        """Keep a completed run's disposition history in its archived record."""
        with self.lock:
            job = self._read(result.get("run_id"))
            if job and job["status"] == "completed":
                job.update(result=result, updated_at_utc=utc_now())
                self._write(job)


JOBS = DiscoveryJobs()
