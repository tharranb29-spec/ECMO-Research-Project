import json
import tempfile
import threading
import unittest
from pathlib import Path

from track3_discovery_jobs import DiscoveryJobs


class DiscoveryJobsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_completion_is_archived_and_survives_process_restart(self):
        saved = []
        finished = threading.Event()

        def runner(query, **kwargs):
            kwargs["progress"]("identity_and_queue_gates")
            return {"run_id": kwargs["run_id"], "query": query, "workflow_state": "cached_demo"}

        def save(result):
            saved.append(result)
            finished.set()

        jobs = DiscoveryJobs(self.path, runner=runner, save_latest=save)
        accepted = jobs.submit("A2A", [], "demo")
        self.assertRegex(accepted["run_id"], r"^shadow:[0-9a-f]{24}$")
        self.assertTrue(finished.wait(2))
        # The save callback runs before the archive write.
        for _ in range(100):
            record = jobs.get(accepted["run_id"])
            if record["status"] == "completed":
                break
            threading.Event().wait(.01)
        self.assertEqual(record["status"], "completed")
        self.assertEqual(saved[0]["run_id"], accepted["run_id"])
        recovered = DiscoveryJobs(self.path, runner=runner, save_latest=save)
        self.assertEqual(recovered.get(accepted["run_id"])["result"]["query"], "A2A")

    def test_cancel_discards_late_provider_output(self):
        started, release = threading.Event(), threading.Event()
        saved = []

        def runner(query, **kwargs):
            started.set()
            release.wait(2)
            return {"run_id": kwargs["run_id"]}

        jobs = DiscoveryJobs(self.path, runner=runner, save_latest=saved.append)
        accepted = jobs.submit("A2A", [], "demo")
        self.assertTrue(started.wait(2))
        cancelled = jobs.cancel(accepted["run_id"])
        release.set()
        for _ in range(100):
            if jobs.active_id is None:
                break
            threading.Event().wait(.01)
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(jobs.get(accepted["run_id"])["status"], "cancelled")
        self.assertEqual(saved, [])

    def test_abandoned_job_is_marked_interrupted_on_restart(self):
        run_id = "shadow:" + "a" * 24
        (self.path / ("a" * 24 + ".json")).write_text(json.dumps({"run_id": run_id, "status": "running"}))
        jobs = DiscoveryJobs(self.path, runner=lambda *_args, **_kwargs: None)
        self.assertEqual(jobs.get(run_id)["status"], "interrupted")
        with self.assertRaisesRegex(ValueError, "Invalid discovery run ID"):
            jobs.get("../../secret")


if __name__ == "__main__":
    unittest.main()
