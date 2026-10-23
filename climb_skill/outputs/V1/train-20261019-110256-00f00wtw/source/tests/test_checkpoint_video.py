"""A saved policy must not silently lose its promised checkpoint recording."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from climb_skill.utils.checkpoint_video import record_checkpoint
from climb_skill.utils.runtime import sha256


class CheckpointVideo(unittest.TestCase):
    def exercise(self, *, returncode=0, missing=0, matching=True, box_height=None, reported_height=None):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "model_100.pt"
            checkpoint.write_bytes(b"test checkpoint")

            def evaluate(command, **kwargs):
                destination = Path(command[command.index("--output") + 1])
                if box_height is not None:
                    self.assertEqual(float(command[command.index("--box-height") + 1]), box_height)
                destination.mkdir()
                (destination / "climb.mp4").write_bytes(b"test video placeholder")
                (destination / "report.json").write_text(json.dumps({
                    "box_height": reported_height if reported_height is not None else box_height,
                    "status": "complete" if not missing else "incomplete",
                    "missing_episodes": missing, "completed_episodes": 4 - missing,
                    "successful_episodes": 0, "video_frames": 600,
                    "checkpoint_sha256": sha256(checkpoint) if matching else "wrong checkpoint",
                }))
                return subprocess.CompletedProcess(command, returncode)

            with patch("climb_skill.utils.checkpoint_video.subprocess.run", side_effect=evaluate):
                if returncode or missing or not matching or (reported_height is not None and reported_height != box_height):
                    with self.assertRaises(RuntimeError):
                        record_checkpoint(checkpoint, device="cuda:0", task="test", episodes=4, box_height=box_height)
                else:
                    result = record_checkpoint(checkpoint, device="cuda:0", task="test", episodes=4, box_height=box_height)
                    self.assertEqual(result["successful_episodes"], 0)
                    self.assertEqual(result["status"], "complete")
            status = json.loads((checkpoint.parent / "checkpoint_videos/model_100.json").read_text())
            self.assertEqual(status["status"], "failed" if returncode or missing or not matching or (reported_height is not None and reported_height != box_height) else "complete")
            self.assertEqual(checkpoint.read_bytes(), b"test checkpoint")

    def test_requested_curriculum_height_is_forwarded_and_checked(self):
        self.exercise(box_height=.05)
        self.exercise(box_height=.05, reported_height=.2)

    def test_zero_success_is_valid_recording(self):
        self.exercise()

    def test_failed_child_does_not_silently_continue(self):
        self.exercise(returncode=1)

    def test_incomplete_or_wrong_policy_report_is_rejected(self):
        self.exercise(missing=1)
        self.exercise(matching=False)


if __name__ == "__main__":
    unittest.main()
