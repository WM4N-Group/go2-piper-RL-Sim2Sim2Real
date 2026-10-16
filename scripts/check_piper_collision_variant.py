"""Check the native PIPER collision overlay without launching Isaac Sim."""

from pathlib import Path
import tempfile
import unittest

from pxr import Usd, UsdPhysics
import torch

from create_piper_collision_variant import SOURCE, create_variant, unmatched_contact_force


class PiperCollisionVariantTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / "piper_self_collision.usda"
        self.report = create_variant(SOURCE, self.output)
        self.stage = Usd.Stage.Open(str(self.output))

    def filtered(self, first, second):
        prim = self.stage.GetPrimAtPath(f"/go2_piper/{first}")
        targets = UsdPhysics.FilteredPairsAPI(prim).GetFilteredPairsRel().GetTargets()
        return self.stage.GetPrimAtPath(f"/go2_piper/{second}").GetPath() in targets

    def test_self_collisions_are_enabled(self):
        for path in self.report["articulation_roots"]:
            self.assertTrue(self.stage.GetPrimAtPath(path).GetAttribute("physxArticulation:enabledSelfCollisions").Get())

    def test_leg_and_adjacent_pairs_remain_filtered(self):
        for first, second in (("base", "FL_thigh"), ("FR_calf", "RL_foot"), ("base", "link0"), ("link2", "link3"), ("link6", "end_effector")):
            with self.subTest(first=first, second=second):
                self.assertTrue(self.filtered(first, second))
                self.assertTrue(self.filtered(second, first))

    def test_arm_body_and_nonadjacent_arm_pairs_are_enabled(self):
        for first, second in (("base", "link2"), ("FL_thigh", "link0"), ("FR_calf", "link4"), ("link2", "link5")):
            with self.subTest(first=first, second=second):
                self.assertFalse(self.filtered(first, second))
                self.assertFalse(self.filtered(second, first))

    def test_original_physical_properties_are_preserved(self):
        self.assertEqual(self.report["body_count"], 25)
        self.assertGreater(self.report["preserved_attributes"], 100)
        original = Usd.Stage.Open(str(SOURCE))
        self.assertFalse(original.GetPrimAtPath("/go2_piper/base").GetAttribute("physxArticulation:enabledSelfCollisions").Get())

    def test_existing_artifact_is_not_overwritten(self):
        with self.assertRaises(FileExistsError):
            create_variant(SOURCE, self.output)

    def test_valid_box_force_is_removed_but_transient_other_force_is_retained(self):
        allowed = torch.zeros((2, 5, 3))
        allowed[:, :, 0] = -12.0
        total = allowed.clone()
        total[1, 2, 2] = 3.0
        torch.testing.assert_close(unmatched_contact_force(total, allowed), torch.tensor([0.0, 3.0]))
        torch.testing.assert_close(allowed[:, :, 2], torch.zeros((2, 5)))

    def test_mismatched_contact_history_is_rejected(self):
        with self.assertRaises(ValueError):
            unmatched_contact_force(torch.zeros((1, 5, 3)), torch.zeros((1, 3, 3)))


if __name__ == "__main__":
    unittest.main()