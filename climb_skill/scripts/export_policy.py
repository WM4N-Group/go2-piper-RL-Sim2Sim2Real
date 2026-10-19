"""Export the history-conditioned 923 -> 18 actor, including encoders and velocity estimator."""

import argparse
from pathlib import Path
import torch

from climb_skill.tasks.direct.climb_skill.task_parameters import OBSERVATIONS
from climb_skill.learning.actor_critic import ClimbActorCritic
from climb_skill.utils.runtime import load_checkpoint, output_directory, sha256, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    torch.set_num_threads(4)
    saved = load_checkpoint(args.checkpoint)
    actor = ClimbActorCritic(saved["configuration"]["ppo"]["initial_std"])
    actor.load_state_dict(saved["model"])
    actor.eval()
    output = output_directory(args.output, "export")
    with torch.no_grad():
        traced = torch.jit.trace(actor, torch.zeros(1, OBSERVATIONS))
        example = torch.randn(4, OBSERVATIONS)
        torch.testing.assert_close(traced(example), actor(example))
        assert not torch.count_nonzero(traced(example)[:, 12:])
    traced.save(str(output / "actor.pt"))
    write_json(output / "contract.json", {**saved["configuration"], "checkpoint_sha256": sha256(args.checkpoint),
               "actor_sha256": sha256(output / "actor.pt"), "policy_branch": "history",
               "arm_semantics": "six zero residuals; keep initial arm joint angles relative to base",
               "observation_warning": "923-dimensional CLIMB contract; incompatible with old 253/304-dimensional skills"})
    print(output)


if __name__ == "__main__":
    main()
