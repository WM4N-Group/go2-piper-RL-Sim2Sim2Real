Changelog
---------

Unreleased: motion_amp_v3 (2026-10-22)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Signed actual-motion rewards replace broad exponential tracking bonuses.
* Add backward/lateral/turning reference clips from the pinned WMP source.
* Condition AMP on requested behavior; gate positive style by actual response.
* Qualify curriculum by sustained directional response and stopping, not exact RMSE.
* Keep 315/324 observations, 12-to-18 action contract and robot physics unchanged.
* Checkpoints/videos every 100 iterations; V2 training cannot be resumed as V3.

velocity_amp_v2 (2026-10-22)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Replace goal-conditioned policy with body velocity commands and tracking curriculum.
* Actor predicts 12 leg residuals, appends six zeros; external action remains 18D.
* Actor/critic observations now 315/324; old goal checkpoints are incompatible.
* Train standing, straight walking, both turning directions and command transitions.
* Video cases now exercise velocity tracking and braking; navigation wrapper is deferred.

0.1.0 (2026-10-22)
~~~~~~~~~~~~~~~~~~

* Generated Isaac Lab external DirectRLEnv package and replaced example task.
* Goal-conditioned Go2-Piper navigation, 18 actions with six arm residuals fixed zero.
* PPO and leg AMP, goal curriculum, stopping posture and explicit arrival hold.
* Checkpoints and independent video every 100 iterations; complete optimizer/curriculum resume.
