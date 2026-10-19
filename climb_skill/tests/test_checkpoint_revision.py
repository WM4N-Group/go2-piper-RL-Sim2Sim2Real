"""Keep restored task checkpoints separate from the discarded v2 candidate."""

import unittest
from climb_skill.tasks.direct.climb_skill.task_parameters import (
    TaskConfig, PPOConfig, configuration, require_implementation,
)


class CheckpointRevision(unittest.TestCase):
    def test_forward_checkpoint_is_accepted(self):
        require_implementation(configuration(TaskConfig(), PPOConfig()))

    def test_standing_checkpoints_cannot_resume_under_forward_task(self):
        for revision in (None, "climb_skill_v1", "climb_skill_v2", "climb_skill_v3_forward"):
            with self.assertRaisesRegex(ValueError, "archived matching source"):
                require_implementation({"implementation_revision": revision})
