"""CPU checks of crawl contact sequencing and reference safety bounds."""
import importlib.util
from pathlib import Path
import unittest
import torch

PATH = Path(__file__).resolve().parents[1] / "source/LeggedManip_Lab/LeggedManip_Lab/tasks/manager_based/leggedmanip_lab/mdp/crawl_gait.py"
spec = importlib.util.spec_from_file_location("crawl_gait", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CrawlTests(unittest.TestCase):
    def test_landing_gate_cannot_switch_on_touch_without_confirmed_load(self):
        clock=module.CrawlClock(1,'cpu');active=torch.tensor([True]);contacts=torch.ones(1,4,dtype=torch.bool)
        clock.elapsed[:]=clock.transfer+clock.swing;clock.lifted[:]=True
        for _ in range(100):clock.update(contacts,active,.02,settle_ready=~active)
        self.assertEqual(clock.leg.item(),0)
        clock.update(contacts,active,.02,settle_ready=active)
        self.assertEqual(clock.leg.item(),3)

    def test_real_foot_must_catch_up_before_translation_and_lowering(self):
        clock = module.CrawlClock(1, "cpu")
        active = torch.tensor([True])
        contacts = torch.ones(1, 4, dtype=torch.bool)
        for _ in range(100):
            clock.update(contacts, active, .02, lift_ready=~active, traverse_ready=~active)
        self.assertAlmostEqual(clock.progress.item(), .25)
        self.assertFalse(clock.lifted.item())
        contacts[0, 0] = False
        for _ in range(100):
            clock.update(contacts, active, .02, lift_ready=active, traverse_ready=~active)
        self.assertAlmostEqual(clock.progress.item(), .75)
        self.assertTrue(clock.lifted.item())
        for _ in range(100):
            clock.update(contacts, active, .02, lift_ready=active, traverse_ready=active)
        self.assertEqual(clock.progress.item(), 1.)
        self.assertEqual(clock.leg.item(), 0)
        contacts[0, 0] = True
        for _ in range(8):
            clock.update(contacts, active, .02, lift_ready=~active, traverse_ready=~active)
        self.assertEqual(clock.leg.item(), 3)

    def test_no_time_only_switch_or_unsupported_swing(self):
        clock = module.CrawlClock(2, "cpu")
        contacts = torch.ones(2, 4, dtype=torch.bool)
        active = torch.ones(2, dtype=torch.bool)
        contacts[1, 3] = False
        for _ in range(100):
            clock.update(contacts, active, .02)
        self.assertEqual(clock.index.tolist(), [0, 0])
        self.assertEqual(clock.elapsed[1].item(), 0)
        contacts[0, 0] = False
        clock.update(contacts, active, .02)
        contacts[0, 0] = True
        for _ in range(8):
            clock.update(contacts, active, .02)
        self.assertEqual(clock.leg.tolist(), [3, 0])
        clock.reset(torch.tensor([0]))
        self.assertEqual(clock.leg.tolist(), [0, 0])
        self.assertFalse(clock.lifted.any())

    def test_limits_under_abrupt_reversals(self):
        torch.manual_seed(8)
        q = torch.zeros(16, 18)
        v = torch.zeros_like(q)
        low, high = q - 1, q + 1
        vmax, amax = torch.full((1, 18), 2.5), torch.full((1, 18), 15.)
        for step in range(600):
            target = torch.full_like(q, 4 if (step // 75) % 2 else -4)
            new_q, new_v = module.limit_reference(q, v, target, low, high, vmax, amax, .02)
            self.assertTrue(((new_q >= low - 1e-6) & (new_q <= high + 1e-6)).all())
            self.assertTrue((new_v.abs() <= vmax + 1e-5).all())
            self.assertTrue(((new_v - v).abs() <= amax * .02 + 1e-5).all())
            torch.testing.assert_close(new_q - q, new_v * .02, atol=1e-6, rtol=1e-5)
            q, v = new_q, new_v

    def test_swing_clears_riser_before_translation(self):
        start = torch.tensor([[.6, .1, .0225]])
        landing = torch.tensor([[.85, .1, .2225]])
        first = module.swing_reference(start, landing, torch.tensor([0.]))
        raised = module.swing_reference(start, landing, torch.tensor([.25]))
        across = module.swing_reference(start, landing, torch.tensor([.75]))
        last = module.swing_reference(start, landing, torch.tensor([1.]))
        torch.testing.assert_close(first, start)
        torch.testing.assert_close(last, landing)
        self.assertAlmostEqual(raised[0, 0].item(), .6, places=6)
        self.assertAlmostEqual(across[0, 0].item(), .85, places=6)
        self.assertGreater(raised[0, 2].item(), .29)
        self.assertGreater(across[0, 2].item(), .29)


if __name__ == "__main__":
    unittest.main()
