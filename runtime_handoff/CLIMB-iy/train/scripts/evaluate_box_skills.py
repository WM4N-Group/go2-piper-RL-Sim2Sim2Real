"""Deterministic physical evaluation of the separate box-skill actors."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import runpy
import traceback

from isaaclab.app import AppLauncher


parser = argparse.ArgumentParser()
parser.add_argument("--task", required=True, choices=("GO2-ARX5-Box-Climb-Play", "GO2-ARX5-Box-Push-Play", "GO2-ARX5-Box-Push-Hybrid-Play", "GO2-PIPER-Box-Climb-Play", "GO2-PIPER-Box-Climb-Smooth-Play", "GO2-PIPER-Box-Climb-Crawl-Play", "GO2-PIPER-Box-Climb-Stages-Play", "GO2-PIPER-Box-Climb-Robust-Play", "GO2-PIPER-Box-Climb-Contact-Robust-Play", "GO2-PIPER-Box-Push-Hybrid-Play", "GO2-PIPER-Box-Push-Tracking-Play", "GO2-PIPER-Box-Push-Low-Play"))
source_group = parser.add_mutually_exclusive_group(required=True)
source_group.add_argument("--checkpoint", type=Path)
source_group.add_argument("--actor-policy", type=Path, help="Diagnostic: directly evaluate a provenance-recorded TorchScript skill actor.")
source_group.add_argument("--locomotion-policy", type=Path, help="Use the frozen 210-input NAV actor for legs; requires --arm-ik.")
parser.add_argument("--output-json", type=Path, required=True)
parser.add_argument("--summary-log", action="store_true", help="Keep the complete JSON report on disk; print only a compact completion summary instead of duplicating dense traces in stdout.")
parser.add_argument("--num_envs", type=int, default=32)
parser.add_argument("--inspect-env-index", type=int, default=0, help="Environment whose trace and optional video are recorded; batch evaluation remains unchanged.")
parser.add_argument("--inspect-extra-env-indices", type=int, nargs="*", default=[], help="Additional environment traces only; camera and batch control remain unchanged.")
parser.add_argument("--inspect-dense-after-s", type=float, help="Record each control step for the inspected environment after this elapsed time; diagnostic telemetry only.")
parser.add_argument("--failure-history-steps", type=int, default=0, help="PIPER Tracking: keep this many pre-step states per failed episode; zero disables (maximum 256).")
parser.add_argument("--steps", type=int, default=1200)
parser.add_argument("--episodes-per-env", type=int, default=1)
parser.add_argument("--episode-length-s", type=float)
parser.add_argument("--preparation-seconds", type=float, default=0.0)
parser.add_argument("--seed", type=int, default=100)
parser.add_argument("--box-height", type=float)
parser.add_argument("--approach-height", type=float, default=0.0)
parser.add_argument("--approach-gap", type=float, default=0.0)
parser.add_argument("--landing-length", type=float)
parser.add_argument("--landing-width", type=float)
parser.add_argument("--start-clearance", type=float)
parser.add_argument("--base-start-x", type=float)
parser.add_argument("--climb-stage-bank", type=Path, help="Training-start diagnostic only; never original-start acceptance.")
parser.add_argument("--climb-stage-guidance", action="store_true", help="Diagnostic support transfer and leg IK; requires Stages task.")
parser.add_argument("--climb-guidance-loaded-start", action="store_true", help="Diagnostic: capture stable loaded posture and preserve PD load offsets during guidance.")
parser.add_argument("--climb-guidance-forward-lift", action="store_true", help="Diagnostic: move the foot forward before crossing the box face while lifting.")
parser.add_argument("--climb-guidance-body-clearance", type=float, default=.34)
parser.add_argument("--climb-guidance-force-balance", action="store_true", help="Diagnostic: recompute gravity/support load compensation as the selected foot unloads.")
parser.add_argument("--climb-guidance-horizontal-balance", action="store_true", help="Diagnostic: include bounded horizontal support force and its moments.")
parser.add_argument("--climb-guidance-preunload", action="store_true", help="Diagnostic: finish measured support transfer before starting the foot lift.")
parser.add_argument("--climb-guidance-landing-contact", action="store_true", help="Diagnostic: bounded downward contact search and confirmed load transfer before switching feet.")
parser.add_argument("--climb-guidance-mixed-height", action="store_true", help="Diagnostic: reference body height to the lower feet during mixed-height support.")
parser.add_argument("--climb-guidance-support-feedback", action="store_true", help="Diagnostic: recapture bounded COM transfer and gate unloading by measured support.")
parser.add_argument("--climb-guidance-support-plane", action="store_true", help="Diagnostic: pitch and raise the body along mixed front/rear support heights.")
parser.add_argument("--climb-guidance-plane-fraction", type=float, default=1., help="Diagnostic: fraction of support-plane pitch and elevation, in [0, 1].")
parser.add_argument("--climb-guidance-feasible-pose", action="store_true", help="Diagnostic: select mixed-support body poses with nominal and estimated loaded joint margin.")
parser.add_argument("--climb-guidance-body-collision", action="store_true", help="Diagnostic: require sampled base-box clearance and joint feasibility during body transfer.")
parser.add_argument("--climb-guidance-independent-height", action="store_true", help="Diagnostic: search height independently of pitch only when the original guarded poses are infeasible.")
parser.add_argument("--climb-guidance-leg-collision", action="store_true", help="Diagnostic: check hip/thigh/calf path clearance and try shorter body transfers when full shifts are infeasible.")
parser.add_argument("--climb-guidance-primitive-collision", action="store_true", help="Diagnostic: retain exact cylinder support radii and USD primitive frames in leg clearance checks.")
parser.add_argument("--climb-guidance-load-preview", action="store_true", help="Diagnostic: preview tripod load targets, search bounded forward body poses, and recover from blocked unloading.")
parser.add_argument("--climb-guidance-swing-preview", action="store_true", help="Diagnostic: tuck ascending rear swing inward6cm and require full sampled joint/leg clearance before unloading.")
parser.add_argument("--climb-guidance-swing-transfer", action="store_true", help="Diagnostic: permit improving four-foot body transfers while rear swing is not yet feasible; unloading still requires full swing clearance.")
parser.add_argument("--climb-guidance-last-pose-search", action="store_true", help="Diagnostic: expand last rear support pose search after original guarded candidates fail.")
parser.add_argument("--climb-guidance-refine-height", action="store_true", help="Diagnostic: retry failed support poses with2.5mm heights, only if the initial body/leg clearance already passes original reserves.")
parser.add_argument("--climb-guidance-endpoint-leg-reserve", action="store_true", help="Diagnostic: prefer10mm leg clearance at a narrow rear ground-foot support-transfer endpoint; preserve the original5mm path guard.")
parser.add_argument("--climb-guidance-endpoint-body-reserve", action="store_true", help="Diagnostic: prefer15mm body clearance at a narrow rear ground-foot transfer endpoint; preserve the original10mm path guard.")
parser.add_argument("--climb-guidance-platform-load-reserve", action="store_true", help="Diagnostic: retry narrow platform-extension tripod plans for80mrad loaded command/torque reserve, keeping the original path and measured gates.")
parser.add_argument("--climb-platform-front-first", action="store_true", help="Diagnostic: after four-foot landing, defer extra leveling and forward body/COM plans until both front feet have advanced and reloaded; preserve original lift readiness gates.")
parser.add_argument("--climb-platform-final-adjust", action="store_true", help="Diagnostic: after both front steps settle, move the body at most1cm forward/up per checked segment toward a fixed4cm advance and nominal clearance.")
parser.add_argument("--climb-guidance-platform-support-recovery", action="store_true", help="Diagnostic: allow a planted weak foot to regain load monotonically during platform transfer, requiring all four endpoint loads>=8N and retaining other path guards.")
parser.add_argument("--climb-guidance-platform-support-path", action="store_true", help="Diagnostic: require all four planted feet to retain positive predicted loads throughout platform-extension support transfer.")
parser.add_argument("--climb-guidance-front-ascent-pose", action="store_true", help="Diagnostic: during an existing four-contact capture, replace an unsafe initial front swing plan only with a fully guarded loaded pose; keep original landing and gates.")
parser.add_argument("--climb-guidance-pose-fixtures", action="store_true", help="Read-only diagnostic: save first infeasible support-pose inputs and up to64 platform-extension planning inputs per environment.")
parser.add_argument("--climb-guidance-retain-infeasible-reference", action="store_true", help="Diagnostic: preserve an existing valid support reference when a calm four-contact replan has no feasible candidate; keep lift blocked and retry at most every1.5s.")
parser.add_argument("--climb-guidance-single-front-pose", action="store_true", help="Diagnostic: apply guarded support pose search when exactly one front foot is planted on the platform, before lifting the other.")
parser.add_argument("--climb-guidance-front-force-trim", action="store_true", help="Diagnostic: bounded measured-force correction only for stalled front-foot ascent unloading; original5N release gate unchanged.")
parser.add_argument("--climb-guidance-front-followup-force-trim", action="store_true", help="Diagnostic: extend bounded front unloading correction to platform front steps with both rear feet on ground; original release and safety gates unchanged.")
parser.add_argument("--climb-guidance-platform-extension-force-trim", action="store_true", help="Diagnostic: existing bounded unload correction for a settled platform front extension stalled after10s; original measured release and all support gates unchanged.")
parser.add_argument("--climb-guidance-platform-extension-tracking", action="store_true", help="Diagnostic: existing slow bounded pose feedback during a stalled platform extension transfer; preserve original arrival and measured unload gates.")
parser.add_argument("--climb-guidance-platform-settled-recovery", action="store_true", help="Diagnostic: start bounded platform residual correction after age3s and measured settling, also after both front steps; original phase gates remain unchanged.")
parser.add_argument("--climb-guidance-platform-final-recovery-rise", action="store_true", help="Diagnostic: after both front steps and loaded residual recovery, permit checked1.5cm vertical final segments; forward cap1cm and original settling gates retained.")
parser.add_argument("--climb-guidance-front-followup-preview", action="store_true", help="Diagnostic: validate mixed-height front followup swing, landing probe/reload and four-support transfer with a10mm nominal swing clearance reserve.")
parser.add_argument("--climb-platform-front-extension", type=float, default=None, help="Separate diagnostic: after four-foot hold and settling, move each front foot forward once by this distance, then hold.")
parser.add_argument("--climb-guidance-platform-level", action="store_true", help="Separate hold diagnostic: guarded25mrad/5mm body leveling segments with all four feet loaded.")
parser.add_argument("--climb-guidance-platform-hold-tracking", action="store_true", help="Diagnostic: bounded slow additional pose feedback only for a calm loaded preextension hold; preserve all original arrival and lift gates.")
parser.add_argument("--climb-guidance-platform-hold-tracking-max-extra", type=float, default=.5, help="Additional Cartesian hold feedback bound in (0,.75]; rate remains.1/s and original gates unchanged.")
parser.add_argument("--climb-guidance-platform-hold", action="store_true", help="Separate diagnostic: hold measured pose after four-foot platform landing and verified reloading; original success unchanged.")
parser.add_argument("--climb-guidance-platform-swing", action="store_true", help="Diagnostic: preview platform swing, existing15mm contact search and loaded landing before lift.")
parser.add_argument("--climb-guidance-platform-pose", action="store_true", help="Diagnostic: keep guarded pose search after all four feet land on the platform; original goal and settle gates remain unchanged.")
parser.add_argument("--climb-guidance-rotate-com", action="store_true", help="Diagnostic: rotate the measured COM offset only for the last ground rear ascent after three feet support on the platform.")
parser.add_argument("--climb-front-raise-height", type=float, help="Diagnostic: measured front hip-to-foot height before rear ascent; four-foot preparation raises front body first.")
parser.add_argument("--climb-last-rear-swing-inset", type=float, help="Diagnostic: inward swing offset for the last ground rear foot only; latched for its complete step.")
parser.add_argument("--climb-guidance-pose-angle-coverage", action="store_true", help="Diagnostic: on failed expanded pose search, sample roll/pitch offsets to.30rad while keeping the original.35rad total angle gate.")
parser.add_argument("--climb-guidance-edge-pose-search", action="store_true", help="Diagnostic: allow guarded fallback for the first rear ascent after both rear feet finish edge preparation.")
parser.add_argument("--climb-rear-edge-prep", action="store_true", help="Diagnostic: prepare both rear feet at existing.69m ground anchors before either ascends.")
parser.add_argument("--climb-rear-ground-stride", type=float, help="Diagnostic: shorter rear ground follow-up only when both front feet support on the platform.")
parser.add_argument("--climb-front-followup", action="store_true", help="Diagnostic: advance front platform anchors after rear ground feet catch up.")
parser.add_argument("--climb-front-followup-target", type=float, help="Diagnostic: cap the second front platform advance to this local x; preserve initial ascent, safety and task success gates.")
parser.add_argument("--climb-rear-ascent-target", type=float, help="Diagnostic: cap only the first rear platform landing; local x must preserve the original .83m edge reserve.")
parser.add_argument("--prepared-starts", type=Path)
parser.add_argument("--prepared-phase", choices=("ground", "platform"), default="ground")
parser.add_argument("--following-platform-height", type=float, default=0.0)
parser.add_argument("--surface-friction", type=float)
parser.add_argument("--box-mass", type=float)
parser.add_argument("--box-friction", type=float)
parser.add_argument("--press-depth", type=float)
parser.add_argument("--push-distance", type=float)
parser.add_argument("--push-height-offset", type=float)
parser.add_argument("--push-hand-pitch", type=float, default=0.8)
parser.add_argument("--push-ik-clearance-minimum", type=float, help="Diagnostic: project unlocked Tracking IK targets onto local body-center clearance constraints.")
parser.add_argument("--push-ik-orientation-weight", type=float, default=1.0, help="Tracking diagnostic: rotation residual scale in pose IK; 1 preserves the original solver.")
parser.add_argument("--push-ik-height-weight", type=float, default=1.0, help="Tracking diagnostic: world height residual weight for bounded IK; no safety threshold changes.")
parser.add_argument("--push-ik-joint-limit-solve", action="store_true", help="Tracking diagnostic: improve the pose solve within the original joint limits.")
parser.add_argument("--push-goal-hold-pose", action="store_true", help="Tracking diagnostic: hold the measured world hand pose on goal entry instead of withdrawing.")
parser.add_argument("--push-goal-brake-gain", type=float, default=0.0, help="Tracking diagnostic: bounded reverse command to brake residual forward base velocity at goal.")
parser.add_argument("--push-goal-release-distance", type=float, default=0.0, help="Tracking diagnostic: small outward hand target offset on goal entry to unload contact.")
parser.add_argument("--push-press-on-legal-contact", action="store_true", help="Tracking diagnostic: sustain pressing on current legal contact even if geometric approach readiness clears.")
parser.add_argument("--push-stop-distance", type=float, default=0.10, help="Tracking diagnostic: controller braking threshold; success criteria stay unchanged.")
parser.add_argument("--push-leg-release-on-contact", action="store_true", help="Tracking diagnostic: start leg action ramp only after real legal hand contact.")
parser.add_argument("--push-contact-memory-s", type=float, default=0.0, help="Tracking diagnostic: retain verified near-face contact briefly for the drive command.")
parser.add_argument("--push-leg-release-ramp-s", type=float, default=0.0, help="Tracking diagnostic: blend in leg actions after arm approach readiness.")
parser.add_argument("--push-leg-contact-ramp-s", type=float, default=0.0, help="Tracking diagnostic: increase leg blending rate during verified legal contact; zero disables.")
parser.add_argument("--push-forward-command-gain", type=float, default=1.0, help="Tracking diagnostic: increase positive base velocity commands while preserving separation and goal stops.")
parser.add_argument("--push-contact-gap-slowdown-start", type=float, default=0.0, help="Tracking diagnostic: cap forward speed below this base-to-face gap during current legal contact; zero disables.")
parser.add_argument("--push-target-maximum-reach", type=float, default=0.0, help="Tracking diagnostic: cap hand target reach in the base yaw frame; zero disables.")
parser.add_argument("--push-body-first", action="store_true", help="Tracking diagnostic: finish SAFE_APPROACH, position the base, then lower the arm to the push face.")
parser.add_argument("--push-velocity-feedback-gain", type=float, default=0.0, help="Tracking diagnostic: add bounded body velocity error feedback to the locomotion command.")
parser.add_argument("--push-velocity-integral-gain", type=float, default=0.0, help="Tracking diagnostic: bounded integral correction for persistent locomotion tracking bias.")
parser.add_argument("--arm-ik", action="store_true", help="Diagnostic: replace the learned arm output with rate-limited differential IK.")
parser.add_argument("--neutral-arm", action="store_true", help="Diagnostic: hold the nominal arm pose for CLIMB.")
parser.add_argument("--neutral-push-command", action="store_true", help="Diagnostic: keep the NAV actor end-effector command at its neutral reference during PUSH.")
parser.add_argument("--observation-noise", action="store_true", help="Diagnostic: retain training observation noise during evaluation.")
parser.add_argument("--video-path", type=Path)
parser.add_argument("--camera-eye", type=float, nargs=3, help="Video camera position relative to inspected environment origin.")
parser.add_argument("--camera-target", type=float, nargs=3, help="Video camera look-at point relative to inspected environment origin.")
parser.add_argument("--video-isolate-environment", action="store_true", help="Hide other environment visuals and command markers in the video; all environments still simulate and are evaluated.")
parser.add_argument("--collision-usd", type=Path)
parser.add_argument("--staged-precontact", action="store_true")
parser.add_argument("--contact-servo", action="store_true")
parser.add_argument("--contact-action-ramp-time", type=float)
parser.add_argument("--neutral-legs", action="store_true")
parser.add_argument("--deployment-actor", type=Path, help="Compare exported TorchScript outputs on every evaluated observation.")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
if args.climb_stage_guidance and args.task != "GO2-PIPER-Box-Climb-Stages-Play":
    parser.error("Stage guidance requires Stages-Play")
if args.climb_guidance_loaded_start and not args.climb_stage_guidance:
    parser.error("Loaded guidance requires --climb-stage-guidance")
if args.climb_guidance_force_balance and not (args.climb_stage_guidance and args.climb_guidance_loaded_start):
    parser.error("Force balance requires stage guidance and loaded start")
if args.climb_guidance_horizontal_balance and not args.climb_guidance_force_balance:
    parser.error("Horizontal balance requires force balance")
if args.climb_guidance_preunload and not args.climb_guidance_force_balance:
    parser.error("Pre-unload requires force balance")
if args.climb_guidance_landing_contact and not args.climb_guidance_preunload:
    parser.error("Landing contact requires pre-unload guidance")
if args.climb_guidance_mixed_height and not args.climb_guidance_landing_contact:
    parser.error("Mixed-height guidance requires landing contact guidance")
if args.climb_guidance_support_feedback and not args.climb_guidance_mixed_height:
    parser.error("Support feedback requires mixed-height guidance")
if args.climb_guidance_support_plane and not args.climb_guidance_support_feedback:
    parser.error("Support plane requires measured support feedback")
if args.climb_guidance_feasible_pose and not args.climb_guidance_support_plane:
    parser.error("Feasible body pose requires support-plane guidance")
if args.climb_guidance_body_collision and not args.climb_guidance_feasible_pose:
    parser.error("Body collision check requires feasible-pose guidance")
if args.climb_guidance_independent_height and not args.climb_guidance_body_collision:
    parser.error("Independent height requires body path collision checks")
if args.climb_guidance_leg_collision and not args.climb_guidance_independent_height:
    parser.error("Leg path collision checks require independent height search")
if args.climb_guidance_primitive_collision and not args.climb_guidance_leg_collision:
    parser.error("Primitive collision checks require leg path collision checks")
if args.climb_guidance_refine_height and not (args.climb_guidance_independent_height
        and args.climb_guidance_load_preview and args.climb_guidance_primitive_collision):
    parser.error("Height refinement requires independent-height and complete loaded/collision previews")
if args.climb_guidance_endpoint_leg_reserve and not (args.climb_guidance_independent_height
        and args.climb_guidance_load_preview and args.climb_guidance_primitive_collision):
    parser.error("Endpoint reserve requires independent-height and complete loaded/collision previews")
if args.climb_guidance_endpoint_body_reserve and not (args.climb_guidance_independent_height
        and args.climb_guidance_load_preview and args.climb_guidance_primitive_collision):
    parser.error("Body endpoint reserve requires independent-height and complete loaded/collision previews")
if args.climb_guidance_platform_load_reserve and not (args.climb_platform_front_extension is not None
        and args.climb_guidance_independent_height and args.climb_guidance_load_preview
        and args.climb_guidance_primitive_collision and args.climb_guidance_swing_preview):
    parser.error("Platform load reserve requires front extension and complete loaded/collision/swing previews")
if args.climb_platform_front_first and not (args.climb_platform_front_extension is not None
        and args.climb_guidance_platform_level and args.climb_guidance_platform_support_path
        and args.climb_guidance_rotate_com):
    parser.error("Front-first ordering requires front extension, leveling, four-support path and rotated COM previews")
if args.climb_guidance_platform_support_recovery and not args.climb_guidance_platform_support_path:
    parser.error("Platform support recovery requires the full four-support path guard")
if args.climb_platform_final_adjust and not args.climb_platform_front_first:
    parser.error("Final platform adjustment requires front-first ordering and all its support/landing guards")
if args.climb_guidance_platform_support_path and not (args.climb_platform_front_extension is not None
        and args.climb_guidance_support_feedback and args.climb_guidance_load_preview
        and args.climb_guidance_rotate_com and args.climb_guidance_primitive_collision
        and args.climb_guidance_swing_preview and args.climb_guidance_landing_contact):
    parser.error("Platform support path requires front extension and complete support/load/COM/collision/swing/landing guards")
if args.climb_guidance_front_ascent_pose and not (args.climb_guidance_support_feedback
        and args.climb_guidance_independent_height and args.climb_guidance_load_preview
        and args.climb_guidance_primitive_collision and args.climb_guidance_swing_preview
        and args.climb_guidance_landing_contact and not args.climb_guidance_single_front_pose):
    parser.error("Front ascent pose requires complete support/load/collision/swing/landing guards and single-front-pose off")
if args.climb_guidance_pose_fixtures and not (args.task == "GO2-PIPER-Box-Climb-Stages-Play"
        and args.episodes_per_env == 1 and args.climb_guidance_load_preview
        and args.climb_guidance_primitive_collision):
    parser.error("Pose fixtures require one episode per environment with stage guidance and complete guarded load previews")
if args.climb_guidance_retain_infeasible_reference and not (args.climb_guidance_support_feedback
        and args.climb_guidance_load_preview and args.climb_guidance_primitive_collision):
    parser.error("Reference retention requires support feedback and complete load/collision previews")
if args.climb_guidance_single_front_pose and not (args.climb_guidance_load_preview
        and args.climb_guidance_primitive_collision and args.climb_guidance_support_plane):
    parser.error("Single-front pose requires complete load and collision path previews")
if args.climb_guidance_front_force_trim and not (args.climb_guidance_preunload
        and args.climb_guidance_support_feedback and args.climb_guidance_primitive_collision
        and args.climb_guidance_load_preview and args.climb_guidance_swing_preview):
    parser.error("Front force trim requires measured unload feedback and all existing load/swing/collision guards")
if args.climb_guidance_front_followup_force_trim and not (args.climb_guidance_front_force_trim
        and args.climb_front_followup and args.climb_guidance_landing_contact
        and args.climb_guidance_mixed_height and args.climb_guidance_platform_hold):
    parser.error("Front followup force trim requires existing force trim, front followup, mixed-height loading, landing confirmation and platform hold")
if args.climb_guidance_front_followup_preview and not (args.climb_front_followup
        and args.climb_guidance_swing_preview and args.climb_guidance_swing_transfer
        and args.climb_guidance_load_preview and args.climb_guidance_rotate_com
        and args.climb_guidance_primitive_collision and args.climb_guidance_independent_height
        and args.climb_guidance_landing_contact and args.climb_guidance_mixed_height
        and args.climb_guidance_platform_hold):
    parser.error("Front followup preview requires complete swing/transfer/load/rotatedCOM/collision/height/landing/mixed-support guards and platform hold")
if args.climb_guidance_platform_extension_force_trim and not (args.climb_guidance_front_force_trim
        and args.climb_platform_front_extension is not None and args.climb_platform_front_first
        and args.climb_guidance_platform_support_path and args.climb_guidance_landing_contact
        and args.climb_guidance_platform_hold):
    parser.error("Platform extension force trim requires existing force trim, front-first extension and original support/landing/hold guards")
if args.climb_guidance_platform_extension_tracking and not (args.climb_guidance_platform_extension_force_trim
        and args.climb_guidance_platform_hold_tracking):
    parser.error("Platform extension tracking requires platform extension force trim and bounded hold tracking")
if args.climb_guidance_platform_settled_recovery and not (args.climb_guidance_platform_extension_tracking
        and args.climb_platform_final_adjust):
    parser.error("Settled platform recovery requires guarded extension tracking and final platform adjustment")
if args.climb_guidance_platform_final_recovery_rise and not args.climb_guidance_platform_settled_recovery:
    parser.error("Final recovery rise requires measured settled platform recovery")
if args.climb_platform_front_extension is not None:
    if not (0. < args.climb_platform_front_extension <= .08):
        parser.error("Platform front extension must be in (0, .08] meters")
    if not (args.climb_guidance_platform_level and args.climb_guidance_swing_preview
            and args.climb_guidance_rotate_com and args.climb_guidance_load_preview):
        parser.error("Platform front extension requires hold leveling, swing/load previews and rotated COM")
if not 0. < args.climb_guidance_platform_hold_tracking_max_extra <= .75:
    parser.error("Platform hold tracking extra gain must be in (0, .75]")
if args.climb_guidance_platform_hold_tracking_max_extra != .5 and not args.climb_guidance_platform_hold_tracking:
    parser.error("Nondefault hold tracking bound requires --climb-guidance-platform-hold-tracking")
if args.climb_guidance_platform_hold_tracking and not (args.climb_platform_front_extension is not None
        and args.climb_guidance_platform_level and args.climb_guidance_platform_support_path
        and args.climb_guidance_force_balance and args.climb_guidance_landing_contact
        and args.climb_guidance_primitive_collision):
    parser.error("Platform hold tracking requires front extension and original platform/load/landing/collision guards")
if args.climb_guidance_platform_level and not (args.climb_guidance_platform_hold and args.climb_guidance_primitive_collision):
    parser.error("Platform leveling requires platform hold and complete collision path checks")
if args.climb_guidance_platform_hold and not args.climb_guidance_mixed_height:
    parser.error("Platform hold requires loaded guidance and landing-contact confirmation")
if args.climb_guidance_platform_swing and not (args.climb_guidance_platform_pose and args.climb_guidance_swing_preview):
    parser.error("Platform swing checking requires platform pose and swing preview")
if args.climb_guidance_platform_pose and not args.climb_guidance_load_preview:
    parser.error("Platform pose checking requires the complete guarded load-preview chain")
if args.climb_guidance_rotate_com and args.climb_front_raise_height is None:
    parser.error("Rotated COM diagnostic requires front-body rise preparation")
if args.climb_front_raise_height is not None:
    if not args.climb_guidance_pose_angle_coverage or not .20 <= args.climb_front_raise_height <= .30:
        parser.error("Front raise requires guarded angle coverage and a height between.20 and.30m")
if args.climb_last_rear_swing_inset is not None:
    if not args.climb_guidance_pose_angle_coverage or not 0. <= args.climb_last_rear_swing_inset <= .06:
        parser.error("Last rear inset requires angle coverage and a value between0 and.06m")
if args.climb_guidance_pose_angle_coverage and not args.climb_guidance_edge_pose_search:
    parser.error("Pose angle coverage requires guarded edge pose search")
if args.climb_guidance_edge_pose_search and not args.climb_rear_edge_prep:
    parser.error("Edge pose search requires rear edge preparation and its original guards")
if args.climb_rear_edge_prep and not args.climb_guidance_last_pose_search:
    parser.error("Rear edge preparation requires guarded expanded pose search")
if args.climb_guidance_last_pose_search and not args.climb_guidance_swing_transfer:
    parser.error("Last rear pose search requires swing transfer and its path guards")
if args.climb_guidance_swing_transfer and not args.climb_guidance_swing_preview:
    parser.error("Swing transfer requires swing preview")
if args.climb_guidance_swing_preview and not (args.climb_guidance_load_preview and args.climb_guidance_forward_lift):
    parser.error("Swing preview requires load preview and forward lift")
if args.climb_guidance_load_preview and not args.climb_guidance_primitive_collision:
    parser.error("Load preview requires primitive path collision checks")
if args.climb_rear_ascent_target is not None and not (args.climb_front_followup and .83 <= args.climb_rear_ascent_target <= 1.05):
    parser.error("Rear ascent target requires front followup and local x in [.83,1.05]")
if args.climb_front_followup_target is not None and not (args.climb_front_followup and 1.10 <= args.climb_front_followup_target <= 1.40):
    parser.error("Front followup target requires front followup and must be in[1.10,1.40]")
if args.climb_front_followup and not args.climb_guidance_support_feedback:
    parser.error("Front follow-up requires measured support feedback")
if not math.isfinite(args.climb_guidance_plane_fraction) or not 0 <= args.climb_guidance_plane_fraction <= 1:
    parser.error("Support-plane fraction must be in [0, 1]")
if args.climb_guidance_plane_fraction != 1 and not args.climb_guidance_support_plane:
    parser.error("Support-plane fraction requires support-plane guidance")
if args.climb_rear_ground_stride is not None and (not args.climb_guidance_support_feedback
        or not math.isfinite(args.climb_rear_ground_stride) or not .06 <= args.climb_rear_ground_stride <= .22):
    parser.error("Rear ground stride requires support feedback and a stride in [.06, .22]")
if args.climb_guidance_forward_lift and not args.climb_stage_guidance:
    parser.error("Forward lift requires --climb-stage-guidance")
if not math.isfinite(args.climb_guidance_body_clearance) or not .20 <= args.climb_guidance_body_clearance <= .40:
    parser.error("Guidance body clearance must be within .20 to .40m")
if args.climb_stage_bank and args.task != "GO2-PIPER-Box-Climb-Stages-Play":
    parser.error("Stage bank requires the isolated Stages task")
if args.video_isolate_environment and args.video_path is None:
    parser.error("--video-isolate-environment requires --video-path")
if args.arm_ik and "Push" not in args.task:
    parser.error("--arm-ik only applies to PUSH")
if args.neutral_arm and "Climb" not in args.task:
    parser.error("--neutral-arm only applies to CLIMB")
if args.neutral_push_command and "Push" not in args.task:
    parser.error("--neutral-push-command only applies to PUSH")
if args.arm_ik and ("Hybrid" in args.task or "Push-Tracking" in args.task or "Push-Low" in args.task):
    parser.error("The hybrid task already contains its arm controller")
if args.locomotion_policy is not None and not args.arm_ik:
    parser.error("--locomotion-policy requires --arm-ik")
if args.output_json.exists():
    parser.error("Output file already exists")
if args.collision_usd is not None and (not args.task.startswith("GO2-PIPER-") or not args.collision_usd.is_file()):
    parser.error("Collision diagnostics require a PIPER task and an existing USD")
if args.staged_precontact and (args.collision_usd is None or "Push-Hybrid" not in args.task):
    parser.error("Staged precontact requires the collision-enabled PIPER hybrid PUSH diagnostic")
if (args.contact_servo or args.contact_action_ramp_time is not None or args.neutral_legs) and not args.staged_precontact:
    parser.error("Contact servo, action ramp time and neutral legs require the staged precontact diagnostic")
if args.contact_action_ramp_time is not None and (not math.isfinite(args.contact_action_ramp_time) or args.contact_action_ramp_time <= 0.0):
    parser.error("Contact action ramp time must be finite and positive")
if args.video_path is not None:
    if args.video_path.exists():
        parser.error("Video file already exists")
    args.enable_cameras = True
if args.steps < 1 or args.num_envs < 1 or args.episodes_per_env < 1:
    parser.error("Evaluation size must be positive")
if args.inspect_dense_after_s is not None and (not math.isfinite(args.inspect_dense_after_s) or args.inspect_dense_after_s < 0):
    parser.error("Dense trace start must be finite and nonnegative")
if not 0 <= args.inspect_env_index < args.num_envs:
    parser.error("Inspect environment index must be in [0, num_envs)")
if args.inspect_extra_env_indices and "Climb" not in args.task:
    parser.error("Additional traces currently support CLIMB only")
if any(not 0 <= i < args.num_envs for i in args.inspect_extra_env_indices):
    parser.error("Extra inspect indices must be in [0, num_envs)")
if not math.isfinite(args.preparation_seconds) or args.preparation_seconds < 0.0:
    parser.error("Preparation duration must be finite and nonnegative")
if args.preparation_seconds and ("Climb" not in args.task or args.episodes_per_env != 1):
    parser.error("Explicit preparation currently supports one CLIMB episode per environment")
for value in (args.box_height, args.box_mass, args.box_friction, args.episode_length_s, args.landing_length, args.landing_width, args.start_clearance, args.surface_friction):
    if value is not None and (not math.isfinite(value) or value <= 0.0):
        parser.error("Physical parameters must be positive and finite")
for value in (args.approach_height, args.approach_gap, args.following_platform_height):
    if not math.isfinite(value) or value < 0.0:
        parser.error("Approach height and gap must be finite and nonnegative")
if args.base_start_x is not None and (not math.isfinite(args.base_start_x) or abs(args.base_start_x) > 0.30):
    parser.error("Base start x must be finite and within 0.30 m of the nominal origin")
for value in (args.press_depth, args.push_distance):
    if value is not None and (not math.isfinite(value) or value <= 0.0):
        parser.error("PUSH parameters must be positive and finite")
if args.push_height_offset is not None and (not math.isfinite(args.push_height_offset) or not -0.03 <= args.push_height_offset <= 0.03):
    parser.error("PUSH height offset must be between -0.03 and 0.03 m")
if not math.isfinite(args.push_hand_pitch) or not 0.0 <= args.push_hand_pitch <= 1.2:
    parser.error("PUSH hand pitch must be between 0 and 1.2 rad")
if args.push_height_offset is not None and "Push" not in args.task:
    parser.error("--push-height-offset only applies to PUSH")
if args.push_ik_clearance_minimum is not None:
    if args.task != "GO2-PIPER-Box-Push-Tracking-Play" or not 0.08 < args.push_ik_clearance_minimum <= 0.15:
        parser.error("IK clearance requires PIPER Tracking and a distance in (0.08, 0.15]")
if not 0.0 < args.push_ik_orientation_weight <= 1.0:
    parser.error("IK orientation weight must be in (0, 1]")
if args.push_ik_orientation_weight != 1.0 and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Weighted pose IK requires PIPER Tracking")
if not 1.0 <= args.push_ik_height_weight <= 3.0:
    parser.error("IK height weight must be in [1, 3]")
if args.push_ik_height_weight != 1.0 and not args.push_ik_joint_limit_solve:
    parser.error("IK height weighting requires bounded pose IK")
if args.push_ik_joint_limit_solve and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Bounded pose IK requires PIPER Tracking")
if args.push_press_on_legal_contact and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Contact-sustained pressing requires PIPER Tracking")
if not 0.0 <= args.push_goal_brake_gain <= 2.0 or (args.push_goal_brake_gain and args.task != "GO2-PIPER-Box-Push-Tracking-Play"):
    parser.error("Goal braking requires PIPER Tracking and gain in [0, 2]")
if not 0.0 <= args.push_goal_release_distance <= 0.02 or (args.push_goal_release_distance and not args.push_goal_hold_pose):
    parser.error("Goal contact release requires goal pose hold and distance in [0, .02]")
if args.push_goal_hold_pose and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Goal pose hold requires PIPER Tracking")
if not 0.05 <= args.push_stop_distance <= 0.11:
    parser.error("PUSH control stop distance must be in [0.05, 0.11] metres")
if args.push_stop_distance != 0.10 and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Control stop distance diagnostic requires PIPER Tracking")
if args.push_leg_release_on_contact and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Contact-triggered leg release requires PIPER Tracking")
if not math.isfinite(args.push_contact_memory_s) or not 0.0 <= args.push_contact_memory_s <= 0.2:
    parser.error("Contact memory must be finite and in [0, 0.2] seconds")
if args.push_contact_memory_s and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Contact memory diagnostic requires PIPER Tracking")
if not math.isfinite(args.push_leg_release_ramp_s) or not 0.0 <= args.push_leg_release_ramp_s <= 2.0:
    parser.error("Leg release ramp must be finite and in [0, 2] seconds")
if args.push_leg_release_ramp_s and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Leg release ramp diagnostic requires PIPER Tracking")
if not 0.0 <= args.push_leg_contact_ramp_s <= args.push_leg_release_ramp_s:
    parser.error("Contact leg ramp must be in [0, ordinary leg ramp]")
if args.push_leg_contact_ramp_s and (args.task != "GO2-PIPER-Box-Push-Tracking-Play" or args.push_leg_release_on_contact):
    parser.error("Contact-accelerated blending requires ordinary Tracking leg release")
if not 1.0 <= args.push_forward_command_gain <= 2.0:
    parser.error("PUSH forward command gain must be in [1, 2]")
if args.push_forward_command_gain != 1.0 and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Forward command gain diagnostic requires PIPER Tracking")
if args.push_contact_gap_slowdown_start and (
    args.task != "GO2-PIPER-Box-Push-Tracking-Play"
    or not 0.43 < args.push_contact_gap_slowdown_start <= 0.65
    or args.push_body_first or args.staged_precontact
):
    parser.error("Contact gap slowdown requires ordinary PIPER Tracking and a start in (0.43, 0.65]")
if args.push_target_maximum_reach != 0.0 and (
    args.task != "GO2-PIPER-Box-Push-Tracking-Play" or not 0.43 <= args.push_target_maximum_reach <= 0.65
):
    parser.error("Target reach requires PIPER Tracking and a distance in [0.43, 0.65]")
if args.push_body_first and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Body-first approach diagnostic requires PIPER Tracking")
if not 0.0 <= args.push_velocity_feedback_gain <= 3.0:
    parser.error("PUSH velocity feedback gain must be in [0, 3]")
if args.push_velocity_feedback_gain and args.task != "GO2-PIPER-Box-Push-Tracking-Play":
    parser.error("Velocity feedback diagnostic requires PIPER Tracking")
if not 0.0 <= args.push_velocity_integral_gain <= 3.0:
    parser.error("PUSH velocity integral gain must be in [0, 3]")
if args.push_velocity_integral_gain and not args.push_velocity_feedback_gain:
    parser.error("Integral feedback requires proportional velocity feedback")
if not 0 <= args.failure_history_steps <= 256:
    parser.error("Failure history must contain 0 to 256 pre-step samples")
if args.failure_history_steps and (
    args.task != "GO2-PIPER-Box-Push-Tracking-Play"
    or args.num_envs * args.failure_history_steps > 65536
):
    parser.error("Failure history requires PIPER Tracking and at most 65536 environment-step slots")
launcher = AppLauncher(args)

import gymnasium as gym
import torch

import isaaclab_tasks
from isaaclab.managers import SceneEntityCfg
from isaaclab_tasks.utils import load_cfg_from_registry
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper

import LeggedManip_Lab.tasks
from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp import box_climb, box_push
from box_evaluation_metrics import ClimbGaitTelemetry, EpisodeHistory, EpisodeQuota, JointMotionTelemetry
from create_piper_collision_variant import configure_collision_candidate


def main():
    config = load_cfg_from_registry(args.task, "env_cfg_entry_point")
    if args.climb_stage_guidance:
        config.actions.joint_pos.guidance_enabled = True
        config.actions.joint_pos.transfer_s = 1.5
        config.actions.joint_pos.swing_s = 3.0
        config.actions.joint_pos.guidance_loaded_start = args.climb_guidance_loaded_start
        config.actions.joint_pos.guidance_forward_lift = args.climb_guidance_forward_lift
        config.actions.joint_pos.guidance_body_clearance = args.climb_guidance_body_clearance
        config.actions.joint_pos.guidance_force_balance = args.climb_guidance_force_balance
        config.actions.joint_pos.guidance_horizontal_balance = args.climb_guidance_horizontal_balance
        config.actions.joint_pos.guidance_preunload = args.climb_guidance_preunload
        config.actions.joint_pos.guidance_landing_contact = args.climb_guidance_landing_contact
        config.actions.joint_pos.guidance_mixed_height = args.climb_guidance_mixed_height
        config.actions.joint_pos.guidance_support_feedback = args.climb_guidance_support_feedback
        config.actions.joint_pos.guidance_support_plane = args.climb_guidance_support_plane
        config.actions.joint_pos.guidance_plane_fraction = args.climb_guidance_plane_fraction
        config.actions.joint_pos.guidance_feasible_pose = args.climb_guidance_feasible_pose
        config.actions.joint_pos.guidance_body_collision = args.climb_guidance_body_collision
        config.actions.joint_pos.guidance_independent_height = args.climb_guidance_independent_height
        config.actions.joint_pos.guidance_leg_collision = args.climb_guidance_leg_collision
        config.actions.joint_pos.guidance_primitive_collision = args.climb_guidance_primitive_collision
        config.actions.joint_pos.guidance_load_preview = args.climb_guidance_load_preview
        config.actions.joint_pos.guidance_swing_preview = args.climb_guidance_swing_preview
        config.actions.joint_pos.guidance_swing_transfer = args.climb_guidance_swing_transfer
        config.actions.joint_pos.guidance_last_pose_search = args.climb_guidance_last_pose_search
        config.actions.joint_pos.guidance_edge_pose_search = args.climb_guidance_edge_pose_search
        config.actions.joint_pos.guidance_pose_angle_coverage = args.climb_guidance_pose_angle_coverage
        config.actions.joint_pos.last_rear_swing_inset = args.climb_last_rear_swing_inset
        config.actions.joint_pos.front_raise_height = args.climb_front_raise_height
        config.actions.joint_pos.guidance_rotate_com = args.climb_guidance_rotate_com
        config.actions.joint_pos.guidance_platform_pose = args.climb_guidance_platform_pose
        config.actions.joint_pos.guidance_platform_hold = args.climb_guidance_platform_hold
        config.actions.joint_pos.guidance_platform_level = args.climb_guidance_platform_level
        config.actions.joint_pos.guidance_platform_hold_tracking = args.climb_guidance_platform_hold_tracking
        config.actions.joint_pos.guidance_platform_hold_tracking_max_extra = args.climb_guidance_platform_hold_tracking_max_extra
        config.actions.joint_pos.platform_front_extension = args.climb_platform_front_extension
        config.actions.joint_pos.platform_front_first = args.climb_platform_front_first
        config.actions.joint_pos.platform_final_adjust = args.climb_platform_final_adjust
        config.actions.joint_pos.guidance_front_force_trim = args.climb_guidance_front_force_trim
        config.actions.joint_pos.guidance_front_followup_force_trim = args.climb_guidance_front_followup_force_trim
        config.actions.joint_pos.guidance_platform_extension_force_trim = args.climb_guidance_platform_extension_force_trim
        config.actions.joint_pos.guidance_platform_extension_tracking = args.climb_guidance_platform_extension_tracking
        config.actions.joint_pos.guidance_platform_settled_recovery = args.climb_guidance_platform_settled_recovery
        config.actions.joint_pos.guidance_platform_final_recovery_rise = args.climb_guidance_platform_final_recovery_rise
        config.actions.joint_pos.guidance_front_followup_preview = args.climb_guidance_front_followup_preview
        config.actions.joint_pos.guidance_single_front_pose = args.climb_guidance_single_front_pose
        config.actions.joint_pos.guidance_retain_infeasible_reference = args.climb_guidance_retain_infeasible_reference
        config.actions.joint_pos.guidance_pose_fixtures = args.climb_guidance_pose_fixtures
        config.actions.joint_pos.guidance_refine_height = args.climb_guidance_refine_height
        config.actions.joint_pos.guidance_endpoint_leg_reserve = args.climb_guidance_endpoint_leg_reserve
        config.actions.joint_pos.guidance_endpoint_body_reserve = args.climb_guidance_endpoint_body_reserve
        config.actions.joint_pos.guidance_platform_load_reserve = args.climb_guidance_platform_load_reserve
        config.actions.joint_pos.guidance_front_ascent_pose = args.climb_guidance_front_ascent_pose
        config.actions.joint_pos.guidance_platform_support_path = args.climb_guidance_platform_support_path
        config.actions.joint_pos.guidance_platform_support_recovery = args.climb_guidance_platform_support_recovery
        config.actions.joint_pos.guidance_platform_swing = args.climb_guidance_platform_swing
        config.actions.joint_pos.rear_ground_stride = args.climb_rear_ground_stride
        config.actions.joint_pos.front_followup = args.climb_front_followup
        config.actions.joint_pos.front_followup_target = args.climb_front_followup_target
        config.actions.joint_pos.rear_ascent_target = args.climb_rear_ascent_target
        config.actions.joint_pos.rear_edge_prep = args.climb_rear_edge_prep
    if args.climb_stage_bank:
        training_config = load_cfg_from_registry("GO2-PIPER-Box-Climb-Stages", "env_cfg_entry_point")
        config.climb_stage_bank = str(args.climb_stage_bank)
        config.events.reset_base = None
        config.events.reset_robot_joints = None
        config.events.reset_climb_stages = training_config.events.reset_climb_stages
    config.scene.num_envs = args.num_envs
    trace_index = args.inspect_env_index
    if args.video_path is not None:
        config.viewer.origin_type = "env"
        config.viewer.env_index = trace_index
        if args.video_isolate_environment:
            for command in vars(config.commands).values():
                if hasattr(command, "debug_vis"):
                    command.debug_vis = False
        if "Push" in args.task:
            config.viewer.eye = (2.8, 2.4, 1.7)
            config.viewer.lookat = (0.8, 0.0, 0.25)
    config.seed = args.seed
    config.sim.device = args.device
    config.observations.policy.enable_corruption = args.observation_noise
    if args.push_ik_clearance_minimum is not None:
        config.push_ik_clearance_minimum = args.push_ik_clearance_minimum
    if args.push_ik_orientation_weight != 1.0:
        config.push_ik_orientation_weight = args.push_ik_orientation_weight
    config.push_ik_height_weight = args.push_ik_height_weight
    if args.push_ik_joint_limit_solve:
        config.push_ik_joint_limit_solve = True
    if args.push_goal_hold_pose:
        config.push_goal_hold_pose = True
    config.push_goal_brake_gain = args.push_goal_brake_gain
    config.push_goal_release_distance = args.push_goal_release_distance
    if args.push_press_on_legal_contact:
        config.push_press_on_legal_contact = True
    if args.push_stop_distance != 0.10:
        config.push_stop_distance = args.push_stop_distance
    if args.push_leg_release_on_contact:
        config.push_leg_release_on_contact = True
    if args.push_contact_memory_s:
        config.push_contact_memory_s = args.push_contact_memory_s
    if args.push_leg_release_ramp_s:
        config.push_leg_release_ramp_s = args.push_leg_release_ramp_s
    config.push_leg_contact_ramp_s = args.push_leg_contact_ramp_s
    config.push_contact_gap_slowdown_start = args.push_contact_gap_slowdown_start
    if args.push_forward_command_gain != 1.0:
        config.push_forward_command_gain = args.push_forward_command_gain
    if args.push_target_maximum_reach:
        config.push_target_maximum_reach = args.push_target_maximum_reach
    if args.push_body_first:
        config.push_body_first = True
    if args.push_velocity_feedback_gain:
        config.push_velocity_feedback_gain = args.push_velocity_feedback_gain
    if args.push_velocity_integral_gain:
        config.push_velocity_integral_gain = args.push_velocity_integral_gain
    if args.episode_length_s is not None:
        config.episode_length_s = args.episode_length_s
    climbing = "Climb" in args.task
    hybrid_push = not climbing and any(
        name in args.task for name in ("Push-Hybrid", "Push-Tracking", "Push-Low")
    )
    if args.prepared_starts is not None:
        if not climbing:
            raise ValueError("Prepared starts require the CLIMB task")
        config.prepared_start_path = str(args.prepared_starts)
        config.prepared_start_phase = args.prepared_phase
    if args.start_clearance is not None:
        config.scene.robot.init_state.pos = (*config.scene.robot.init_state.pos[:2], args.start_clearance)
    if args.base_start_x is not None:
        config.scene.robot.init_state.pos = (args.base_start_x, *config.scene.robot.init_state.pos[1:])
    if climbing:
        terrain = config.scene.terrain.terrain_generator.sub_terrains["box"]
        terrain.approach_height = args.approach_height
        terrain.approach_gap = args.approach_gap
        terrain.following_platform_height = args.following_platform_height
        if args.surface_friction is not None:
            config.scene.terrain.physics_material.static_friction = args.surface_friction
            config.scene.terrain.physics_material.dynamic_friction = args.surface_friction
            config.sim.physics_material = config.scene.terrain.physics_material
        if args.landing_length is not None:
            terrain.box_length = args.landing_length
        if args.landing_width is not None:
            terrain.box_width = args.landing_width
    if args.box_height is not None:
        if climbing:
            config.scene.terrain.terrain_generator.sub_terrains["box"].box_height_range = (args.box_height, args.box_height)
        else:
            config.box_size = (*config.box_size[:2], args.box_height)
            config.scene.box.spawn.size = config.box_size
            config.scene.box.init_state.pos = (*config.scene.box.init_state.pos[:2], args.box_height / 2.0)
    if not climbing:
        if args.push_height_offset is not None:
            config.push_hand_height_offset = args.push_height_offset
            if hasattr(config, "push_contact_height_offset"):
                config.push_contact_height_offset = args.push_height_offset
        config.actions.joint_pos.hand_pitch = args.push_hand_pitch
        if args.press_depth is not None:
            config.push_press_depth = args.press_depth
        if args.push_distance is not None:
            config.push_distance = args.push_distance
        if args.box_mass is not None:
            config.scene.box.spawn.mass_props.mass = args.box_mass
        if args.box_friction is not None:
            config.scene.box.spawn.physics_material.static_friction = args.box_friction
            config.scene.box.spawn.physics_material.dynamic_friction = args.box_friction
    collision_variant = configure_collision_candidate(
        config, args.collision_usd, args.staged_precontact, args.contact_servo, args.contact_action_ramp_time,
    ) if args.collision_usd else None
    agent_config = load_cfg_from_registry(args.task, "rsl_rl_cfg_entry_point")
    agent_config.device = args.device
    agent_config.seed = args.seed
    if agent_config.actor.activation != "elu":
        raise ValueError("Evaluation requires the project's ELU actor")
    env = RslRlVecEnvWrapper(gym.make(args.task, cfg=config, render_mode="rgb_array" if args.video_path else None), clip_actions=agent_config.clip_actions)
    base = env.unwrapped
    stage_mass_provenance = None
    stage_action = base.action_manager.get_term("joint_pos")
    if hasattr(stage_action, "mass"):
        actual_mass = base.scene["robot"].root_physx_view.get_masses().to(stage_action.mass.device)
        stage_mass_provenance = dict(
            body_names=base.scene["robot"].body_names,
            cached_at_construction=stage_action.mass.cpu().tolist(),
            actual_after_startup=actual_mass.cpu().tolist())
    video = None
    if args.video_path is not None:
        import imageio.v2 as imageio

        if args.video_isolate_environment:
            from isaacsim.core.utils.stage import get_current_stage
            from pxr import UsdGeom

            stage = get_current_stage()
            for env_index in range(args.num_envs):
                if env_index != trace_index:
                    prim = stage.GetPrimAtPath(f"/World/envs/env_{env_index}")
                    if not prim.IsValid():
                        raise RuntimeError(f"Cannot hide missing environment {env_index}")
                    UsdGeom.Imageable(prim).MakeInvisible()
            # Clones may inherit env_0's visibility; author an explicit visible opinion.
            inspected_prim = stage.GetPrimAtPath(f"/World/envs/env_{trace_index}")
            UsdGeom.Imageable(inspected_prim).CreateVisibilityAttr().Set(UsdGeom.Tokens.inherited)
        args.video_path.parent.mkdir(parents=True, exist_ok=True)
        video = imageio.get_writer(str(args.video_path), fps=round(1.0 / (2 * base.step_dt)), codec="libx264")
        origin = base.scene.env_origins[trace_index].cpu().numpy()
        camera_eye = args.camera_eye if args.camera_eye is not None else ([3.0, 3.0, 1.8] if climbing else [0.7, 3.2, 1.5])
        camera_target = args.camera_target if args.camera_target is not None else [0.9, 0.0, 0.3]
        base.sim.set_camera_view(eye=origin + camera_eye, target=origin + camera_target)
    if args.locomotion_policy is not None:
        policy = torch.jit.load(str(args.locomotion_policy), map_location=args.device).eval()
        observation_groups = ["policy"]
    elif args.actor_policy is not None:
        policy = torch.jit.load(str(args.actor_policy), map_location=args.device).eval()
        observation_groups = agent_config.obs_groups["actor"]
    else:
        checkpoint = torch.load(args.checkpoint, map_location=args.device, weights_only=False)
        load_actor = runpy.run_path(str(Path(__file__).resolve().parent / "rsl_rl/initialization.py"))["actor_from_state_dict"]
        policy = load_actor(checkpoint["actor_state_dict"], device=args.device)
        observation_groups = agent_config.obs_groups["actor"]
    if args.neutral_legs:
        frozen_policy = policy

        def policy(observation):
            return torch.zeros_like(frozen_policy(observation))
    observation = env.get_observations()
    deployment_actor = torch.jit.load(str(args.deployment_actor), map_location=args.device).eval() if args.deployment_actor else None
    deployment_max_error = 0.0
    deployment_comparisons = 0
    robot = base.scene["robot"]
    arm_controller = None
    if args.arm_ik:
        from LeggedManip_Lab.tasks.manager_based.leggedmanip_lab.mdp.box_push_ik import PushArmIK

        arm_controller = PushArmIK(base, hold_legs_until_ready=args.locomotion_policy is not None, lock_arm_on_contact=args.locomotion_policy is not None)
    feet = SceneEntityCfg("robot", body_names=".*_foot")
    feet.resolve(base.scene)
    sensor = SceneEntityCfg("contact_forces", body_names=".*_foot")
    sensor.resolve(base.scene)
    hand = SceneEntityCfg("robot", body_names="end_effector")
    hand.resolve(base.scene)
    arm = SceneEntityCfg("robot", joint_names="joint.*")
    arm.resolve(base.scene)
    quota = EpisodeQuota(args.num_envs, args.episodes_per_env, args.device)
    completions, successes = quota.completed, quota.successful
    platform_duration = torch.zeros((args.num_envs, 2), device=args.device)
    maximum_platform_duration = torch.zeros_like(platform_duration)
    motion = JointMotionTelemetry(robot.data.joint_pos, base.step_dt)
    gait_quality = ClimbGaitTelemetry(args.num_envs, args.device, base.step_dt) if climbing else None

    def sample_gait(active):
        if gait_quality is not None:
            contact = base.scene["contact_forces"].data
            gait_quality.update(active, base.episode_length_buf * base.step_dt,
                                contact.net_forces_w[:, sensor.body_ids],
                                contact.net_forces_w_history[:, :, sensor.body_ids],
                                robot.data.root_lin_vel_w[:, 2])

    def crawl_state():
        if "Climb-Crawl" not in args.task and "Climb-Stages" not in args.task:
            return {}
        action = base.action_manager.get_term("joint_pos")
        return {
            **({"guidance_cached_weight_n": action.mass.sum(1)*9.81,
                "guidance_com_local": action.center_of_mass()-base.scene.env_origins}
               if hasattr(action, "mass") else {}),
            **({"guidance_ground_searches": action.guidance.ground_searches,
                "guidance_ground_applied": action.guidance.ground_applied}
                if getattr(action, "guidance", None) is not None and hasattr(action.guidance, "ground_searches") else {}),
            **({"guidance_platform_searches": action.guidance.platform_searches,
                "guidance_platform_search_applied": action.guidance.platform_search_applied}
                if getattr(action, "guidance", None) is not None and hasattr(action.guidance, "platform_searches") else {}),
            **({"guidance_final_searches": action.guidance.final_searches,
                "guidance_final_search_applied": action.guidance.final_search_applied}
                if getattr(action, "guidance", None) is not None and hasattr(action.guidance, "final_searches") else {}),
            **({"guidance_final_closure_attempts": action.guidance.final_closure_attempts,
                "guidance_final_closure_applied": action.guidance.final_closure_applied}
                if getattr(action,"guidance",None) is not None and hasattr(action.guidance,"final_closure_attempts") else {}),
            **({"guidance_front_angular_scale": action.guidance.front_angular_scale}
                if getattr(action,"guidance",None) is not None and hasattr(action.guidance,"front_angular_scale") else {}),
            **({"guidance_rear_prep_age": action.guidance.rear_prep_age,
                "guidance_rear_prep_active": action.guidance.rear_prep_active,
                "guidance_rear_prep_searches": action.guidance.rear_prep_searches,
                "guidance_rear_prep_applied": action.guidance.rear_prep_applied}
                if getattr(action, "guidance", None) is not None and hasattr(action.guidance, "rear_prep_age") else {}),
            **({"guidance_support_margin": action.guidance.margin,
                "guidance_ik_error": action.guidance.ik_error,
                "guidance_limit_excess": action.guidance.limit_excess}
               if getattr(action, "guidance", None) is not None else {}),
            **({"guidance_engaged": action.guidance.engaged,
                "guidance_valid_legs": action.guidance.valid_legs,
                "guidance_load_bias": action.guidance.load_bias}
               if getattr(action, "guidance", None) is not None and action.cfg.guidance_loaded_start else {}),
            **({"climb_stage_start_id": base.climb_stage_start_id} if hasattr(base, "climb_stage_start_id") else {}),
            **({"guidance_support_loads": action.guidance.support_loads,
                "guidance_load_residual": action.guidance.load_residual,
                "guidance_load_torque": action.guidance.load_torque}
               if getattr(action, "guidance", None) is not None and action.cfg.guidance_force_balance else {}),
            **({"guidance_support_vectors": action.guidance.support_vectors,
                "guidance_wrench_residual": action.guidance.wrench_residual}
               if getattr(action, "guidance", None) is not None and action.cfg.guidance_horizontal_balance else {}),
            **({"guidance_unload_offset_cap_age": action.guidance.stalled_foot_unload.cap_age,
                "guidance_unload_offset_extended": action.guidance.stalled_foot_unload.extended,
                "guidance_unload_offset_m": action.guidance.stalled_foot_unload.applied,
                "guidance_unload_offset_state_m": action.guidance.stalled_foot_unload.offset,
                "guidance_unload_offset_blocked": action.guidance.stalled_foot_unload.blocked,
                "guidance_reference_velocity": action.reference_velocity,
                "guidance_unload_fraction": action.guidance.unload_fraction,
                "guidance_unload_stable": action.guidance.unload_stable}
               if getattr(action, "guidance", None) is not None and action.cfg.guidance_preunload else {}),
            **({"guidance_landing_depth": action.guidance.landing_contact.depth,
                "guidance_touch_age": action.guidance.landing_contact.touch_age,
                "guidance_reload": action.guidance.landing_contact.reload,
                "guidance_loaded_age": action.guidance.landing_contact.loaded_age}
               if getattr(action, "guidance", None) is not None and action.cfg.guidance_landing_contact else {}),
            **({"guidance_body_target": action.guidance.target-base.scene.env_origins,
                "guidance_nominal_joints": action.guidance.nominal_joints,
                "guidance_command_limit_excess": action.guidance.command_limit_excess}
               if getattr(action, "guidance", None) is not None and action.cfg.guidance_mixed_height else {}),
            **({"guidance_target_orientation": action.guidance.target_orientation}
               if getattr(action, "guidance", None) is not None and action.cfg.guidance_support_plane else {}),
            **({"guidance_pose_feasible": action.guidance.pose_feasible,
                "guidance_pose_margin": action.guidance.pose_margin}
               if getattr(action, "guidance", None) is not None and action.cfg.guidance_feasible_pose else {}),
            **({"guidance_pose_path_gap": action.guidance.pose_path_gap,
                "guidance_pose_path_margin": action.guidance.pose_path_margin}
               if getattr(action, "guidance", None) is not None and action.cfg.guidance_body_collision else {}),
            **({"guidance_pose_requested_target": action.guidance.pose_requested_target-base.scene.env_origins,
                "guidance_pose_capture_com": action.guidance.pose_capture_com-base.scene.env_origins}
               if getattr(action, "guidance", None) is not None and action.cfg.guidance_independent_height else {}),
            **({"guidance_pose_leg_path_gap": action.guidance.pose_leg_path_gap}
               if getattr(action, "guidance", None) is not None and action.cfg.guidance_leg_collision else {}),
            **({"guidance_load_replan": action.guidance.load_replan}
               if getattr(action, "guidance", None) is not None and action.cfg.guidance_load_preview else {}),
            **({"guidance_swing_path_margin": action.guidance.swing_path_margin,
                "guidance_swing_path_gap": action.guidance.swing_path_gap,
                "guidance_swing_path_ready": action.guidance.swing_path_ready,
                "guidance_front_raise_height": action.guidance.front_raise_measured_height(),
                "guidance_front_raise_ready": action.guidance.front_raise_ready()}
               if getattr(action, "guidance", None) is not None and action.cfg.guidance_swing_preview else {}),
            **({"guidance_height_refinements": action.guidance.height_refinements}
               if args.climb_guidance_refine_height else {}),
            **({"guidance_endpoint_reserve_attempts": action.guidance.endpoint_reserve_attempts,
                "guidance_endpoint_reserve_applied": action.guidance.endpoint_reserve_applied}
               if args.climb_guidance_endpoint_leg_reserve else {}),
            **({"guidance_body_reserve_attempts": action.guidance.body_reserve_attempts,
                "guidance_body_reserve_applied": action.guidance.body_reserve_applied}
               if args.climb_guidance_endpoint_body_reserve else {}),
            **({"guidance_front_ascent_attempts": action.guidance.front_ascent_attempts,
                "guidance_front_ascent_applied": action.guidance.front_ascent_applied}
               if args.climb_guidance_front_ascent_pose else {}),
            **({"guidance_platform_load_attempts": action.guidance.platform_load_attempts,
                "guidance_platform_load_applied": action.guidance.platform_load_applied}
               if args.climb_guidance_platform_load_reserve else {}),
            **({"guidance_replan_reference_retained": action.guidance.replan_reference_retained,
                "guidance_replan_rejections": action.guidance.replan_rejections,
                "guidance_replan_retry_age": action.guidance.replan_retry_age}
               if args.climb_guidance_retain_infeasible_reference else {}),
            **({"guidance_front_trim_n": action.guidance.force_trim.applied_n,
                "guidance_front_trim_integral_n": action.guidance.force_trim.force_n,
                "guidance_front_trim_stall_s": action.guidance.force_trim.stall_age}
               if args.climb_guidance_front_force_trim else {}),
            **({"platform_hold_active": action.platform_hold} if args.climb_guidance_platform_hold else {}),
            **({"platform_extension_completed": action.extension.completed,
                "platform_extension_moving": action.extension.moving,
                "platform_extension_stable": action.extension.stable,
                "platform_extension_goals": action.extension.goals-base.scene.env_origins[:, None]}
               if args.climb_platform_front_extension is not None else {}),
            **({"platform_hold_tracking_extra": action.guidance.hold_tracking.extra,
                "platform_hold_tracking_stable": action.guidance.hold_tracking.stable,
                "platform_hold_tracking_latched": action.guidance.hold_tracking.latched}
               if args.climb_guidance_platform_hold_tracking else {}),
            **({"platform_level_segments": action.guidance.platform_level_segments} if args.climb_guidance_platform_level else {}),
            **({"platform_final_segments": action.guidance.platform_final_segments,
                "platform_final_rejections": action.guidance.platform_final_rejections,
                "platform_final_started": action.guidance.platform_final_started,
                "platform_final_goal": action.guidance.platform_final_goal-base.scene.env_origins,
                "platform_final_stable": action.guidance.platform_final_stable}
               if args.climb_platform_final_adjust else {}),
            "crawl_leg_index": action.clock.leg,
            "crawl_phase": action.clock.progress,
            "crawl_lifted": action.clock.lifted,
            "crawl_contacts": action.contacts(),
            "crawl_foot_position": action.feet_positions()[action.rows, action.clock.leg] - base.scene.env_origins,
            "crawl_foot_reference": action.foot_reference - base.scene.env_origins,
            **({"guidance_expanded_searches": action.guidance.expanded_searches,
                "guidance_expanded_pose": action.guidance.expanded_pose,
                "guidance_com_rotation_active": action.guidance.com_rotation_active}
               if getattr(action, "guidance", None) is not None and action.cfg.guidance_last_pose_search else {}),
            "crawl_landing_position": action.landing - base.scene.env_origins,
        }
    terminal_states = []
    failure_history = EpisodeHistory(args.num_envs, args.failure_history_steps, args.device) if args.failure_history_steps else None
    failure_histories = []
    original_pre_reset = base.recorder_manager.record_pre_reset

    def sample_motion(active):
        motion.sample(
            active, robot.data.joint_pos_target, robot.data.joint_vel, robot.data.joint_acc,
            robot.data.applied_torque, robot.data.joint_effort_limits, robot.data.root_ang_vel_w,
        )

    def record_pre_reset(env_ids, *arguments, **keywords):
        terminal_active = torch.zeros(args.num_envs, dtype=torch.bool, device=args.device)
        terminal_active[env_ids] = quota.active[env_ids]
        sample_gait(terminal_active)
        if gait_quality is not None:
            gait_quality.reset_episode(env_ids)
        selected = env_ids[quota.active[env_ids]]
        terminal_mask = torch.zeros(args.num_envs, dtype=torch.bool, device=args.device)
        terminal_mask[selected] = True
        sample_motion(terminal_mask)
        fields = {
            "elapsed_seconds": base.episode_length_buf * base.step_dt,
            "robot_position": robot.data.root_pos_w - base.scene.env_origins,
            "robot_quaternion": robot.data.root_quat_w,
            "robot_velocity": robot.data.root_lin_vel_w,
            "robot_gravity": robot.data.projected_gravity_b,
            "robot_joint_position": robot.data.joint_pos,
            "robot_joint_velocity": robot.data.joint_vel,
            "robot_joint_acceleration": robot.data.joint_acc,
            "robot_joint_position_target": robot.data.joint_pos_target,
            "robot_applied_torque": robot.data.applied_torque,
            "robot_angular_velocity": robot.data.root_ang_vel_w,
            "robot_body_position": robot.data.body_pos_w - base.scene.env_origins[:, None, :],
            "body_contact_forces": base.scene["contact_forces"].data.net_forces_w,
            "body_contact_force_history": base.scene["contact_forces"].data.net_forces_w_history,
            "termination_flags": torch.stack([
                base.termination_manager.get_term(name) for name in base.termination_manager.active_terms
            ], dim=1),
        }
        fields.update(crawl_state())
        if hybrid_push:
            controller = base.action_manager.get_term("joint_pos").controller
            fields.update(
                safe_approach_complete=controller.safe_approach_complete,
                safe_approach_index=controller.safe_approach_index,
                precontact_stage=controller.precontact_stage,
                precontact_ready=controller.precontact_ready,
                body_ready=controller.body_ready,
                arm_command_position=controller.target_position - base.scene.env_origins,
                ik_clearance_residual=controller.clearance_residual,
                ik_clearance_correction=controller.clearance_correction,
                ik_clearance_distance=controller.clearance_distance,
                goal_hold_active=controller.goal_hold_active,
                leg_contact_ready=controller.leg_contact_ready,
            )
        if not climbing:
            box = base.scene["box"]
            settle_term = base.termination_manager.get_term_cfg("box_settled").func
            if hasattr(settle_term, "duration"):
                fields["settle_duration"] = settle_term.duration
            target = box_push.push_target(base)
            displacement = box.data.root_pos_w - target
            displacement = displacement.clone()
            displacement[:, 0] += config.push_distance
            terminal_hand_force = base.scene["box_contact_hand"].data.force_matrix_w.sum(dim=(1, 2))
            terminal_contact = base.scene["box_contact_hand"].data.contact_pos_w[:, 0, 0]
            terminal_valid = box_push.hand_contact(base, hand)
            terminal_strength = torch.linalg.vector_norm(terminal_hand_force, dim=1)
            unclassified = (terminal_strength > 1.0) & ~terminal_valid
            unclassified_hand_contact_steps[selected] += unclassified[selected].float()
            maximum_unclassified_hand_force[selected] = torch.maximum(
                maximum_unclassified_hand_force[selected], terminal_strength[selected] * unclassified[selected],
            )
            fields.update(
                box_position=box.data.root_pos_w - base.scene.env_origins,
                box_quaternion=box.data.root_quat_w,
                box_goal=target - base.scene.env_origins,
                box_displacement=displacement,
                box_goal_error=torch.linalg.vector_norm(target[:, :2] - box.data.root_pos_w[:, :2], dim=1),
                box_speed=torch.linalg.vector_norm(box.data.root_lin_vel_w, dim=1),
                box_angular_speed=torch.linalg.vector_norm(box.data.root_ang_vel_w, dim=1),
                hand_force=terminal_hand_force,
                hand_position=robot.data.body_pos_w[:, hand.body_ids[0]] - base.scene.env_origins,
                hand_quaternion=robot.data.body_quat_w[:, hand.body_ids[0]],
                hand_contact_position=torch.nan_to_num(terminal_contact - base.scene.env_origins),
                hand_contact_position_valid=torch.isfinite(terminal_contact).all(dim=1),
                hand_contact_valid=terminal_valid,
            )
        snapshots = quota.terminal_snapshot(env_ids, **fields)
        if failure_history is not None:
            failure_histories.extend(failure_history.finish(
                snapshots, list(base.termination_manager.active_terms), len(terminal_states),
            ))
        terminal_states.extend(snapshots)
        return original_pre_reset(env_ids, *arguments, **keywords)

    base.recorder_manager.record_pre_reset = record_pre_reset
    maximum_forward = torch.full((args.num_envs,), -torch.inf, device=args.device)
    minimum_base_height = torch.full((args.num_envs,), torch.inf, device=args.device)
    maximum_tilt = torch.zeros(args.num_envs, device=args.device)
    maximum_condition = torch.zeros(args.num_envs, device=args.device)
    condition_duration = torch.zeros_like(maximum_condition)
    maximum_support = torch.zeros_like(maximum_condition)
    maximum_joint_velocity = torch.zeros(robot.num_joints, device=args.device)
    maximum_torque_ratio = 0.0
    push_force_sum = torch.zeros(args.num_envs, device=args.device)
    push_contact_steps = torch.zeros_like(push_force_sum)
    maximum_push_force = torch.zeros_like(push_force_sum)
    unclassified_hand_contact_steps = torch.zeros_like(push_force_sum)
    maximum_unclassified_hand_force = torch.zeros_like(push_force_sum)
    reasons = {name: 0 for name in base.termination_manager.active_terms}
    trace_indices = list(dict.fromkeys([trace_index, *args.inspect_extra_env_indices]))
    traces = {i: [] for i in trace_indices}
    with torch.inference_mode():
        for step in range(args.steps):
            active = quota.active.clone()
            sample_gait(active)
            step_samples = {}
            relative = robot.data.root_pos_w - base.scene.env_origins
            maximum_forward[active] = torch.maximum(maximum_forward[active], relative[active, 0])
            minimum_base_height[active] = torch.minimum(minimum_base_height[active], relative[active, 2])
            tilt = torch.acos((-robot.data.projected_gravity_b[:, 2]).clamp(-1.0, 1.0))
            maximum_tilt[active] = torch.maximum(maximum_tilt[active], tilt[active])
            if climbing:
                condition = box_climb.box_standing(base, feet, sensor)
                support = box_climb.supported_feet(base, feet, sensor).sum(dim=1).float()
                maximum_support[active] = torch.maximum(maximum_support[active], support[active])
                # Separate stage diagnostics; original box_standing/termination stays intact.
                on_platform = support == 4
                platform_still = (on_platform & (robot.data.root_lin_vel_w.norm(dim=1) < .15)
                    & (robot.data.root_ang_vel_w.norm(dim=1) < .4)
                    & (robot.data.projected_gravity_b[:, 2] < -.94))
                platform_duration[base.episode_length_buf == 0] = 0.
                platform_duration[:] = torch.where(torch.stack((on_platform, platform_still), 1)
                    & active[:, None], platform_duration+base.step_dt, 0.)
                maximum_platform_duration[:] = torch.maximum(maximum_platform_duration, platform_duration)
            else:
                condition = box_push.hand_contact(base, hand)
                hand_force = base.scene["box_contact_hand"].data.force_matrix_w.sum(dim=(1, 2))
                normal_force = torch.linalg.vector_norm(hand_force, dim=1)
                push_force_sum += normal_force * (condition & active)
                push_contact_steps += (condition & active).float()
                maximum_push_force[active] = torch.maximum(maximum_push_force[active], normal_force[active])
                unclassified = (normal_force > 1.0) & ~condition & active
                unclassified_hand_contact_steps += unclassified.float()
                maximum_unclassified_hand_force = torch.maximum(maximum_unclassified_hand_force, normal_force * unclassified)
            condition_duration = torch.where(condition & active, condition_duration + base.step_dt, 0.0)
            maximum_condition = torch.maximum(maximum_condition, condition_duration)
            maximum_joint_velocity = torch.maximum(maximum_joint_velocity, robot.data.joint_vel[active].abs().max(dim=0).values)
            ratio = robot.data.applied_torque[active].abs() / robot.data.joint_effort_limits[active].clamp_min(1e-6)
            maximum_torque_ratio = max(maximum_torque_ratio, ratio.max().item())
            dense_trace = args.inspect_dense_after_s is not None and step*base.step_dt >= args.inspect_dense_after_s
            for inspect_index in trace_indices:
                if active[inspect_index] and (dense_trace or step < 50 or step % 25 == 0 or (not climbing and normal_force[inspect_index] > 1.0)):
                    sample = {
                        "step": step, "env_id": inspect_index, "robot_position": relative[inspect_index].tolist(),
                        "robot_gravity": robot.data.projected_gravity_b[inspect_index].tolist(),
                        "robot_velocity": robot.data.root_lin_vel_w[inspect_index].tolist(),
                        "robot_angular_velocity": robot.data.root_ang_vel_w[inspect_index].tolist(),
                        "feet_height": (robot.data.body_pos_w[inspect_index, feet.body_ids, 2] - base.scene.env_origins[inspect_index, 2]).tolist(),
                    }
                    if climbing:
                        sample.update(
                            robot_quaternion=robot.data.root_quat_w[inspect_index].tolist(),
                            feet_position=(robot.data.body_pos_w[inspect_index, feet.body_ids]
                                           - base.scene.env_origins[inspect_index]).tolist(),
                            joint_position=robot.data.joint_pos[inspect_index].tolist(),
                            joint_position_target=robot.data.joint_pos_target[inspect_index].tolist(),
                            joint_velocity=robot.data.joint_vel[inspect_index].tolist(),
                            joint_acceleration=robot.data.joint_acc[inspect_index].tolist(),
                            applied_torque=robot.data.applied_torque[inspect_index].tolist(),
                            foot_contact_force_z=base.scene["contact_forces"].data.net_forces_w[inspect_index, sensor.body_ids, 2].tolist(),
                        )
                        sample.update({name: value[inspect_index].tolist() for name, value in crawl_state().items()})
                        guidance = getattr(base.action_manager.get_term("joint_pos"), "guidance", None)
                        if guidance is not None:
                            # Read-only geometry for comparing planned clearance
                            # with the actual pose throughout landing and reloading.
                            sample.update(
                                guidance_body_origin=(guidance.origin[inspect_index]
                                                      - base.scene.env_origins[inspect_index]).tolist(),
                                guidance_origin_orientation=guidance.orientation[inspect_index].tolist(),
                                guidance_anchors=(guidance.anchors[inspect_index]
                                                  - base.scene.env_origins[inspect_index]).tolist(),
                                guidance_reference_age=float(guidance.age[inspect_index]),
                            )
                    if not climbing:
                        action_term = base.action_manager.get_term("joint_pos") if hybrid_push else None
                        controller = action_term.controller if action_term is not None else None
                        target = controller.target_position[inspect_index] if controller is not None else box_push.push_hand_target(base)[inspect_index]
                        sample.update(
                            box_position=(base.scene["box"].data.root_pos_w[inspect_index] - base.scene.env_origins[inspect_index]).tolist(),
                            box_quaternion=base.scene["box"].data.root_quat_w[inspect_index].tolist(),
                            hand_position=(robot.data.body_pos_w[inspect_index, hand.body_ids[0]] - base.scene.env_origins[inspect_index]).tolist(),
                            hand_contact=bool(condition[inspect_index]),
                            approach_completed=bool(base.box_push_approached[inspect_index]),
                            hand_force_world=hand_force[inspect_index].tolist(),
                            hand_contact_position=torch.nan_to_num(
                                base.scene["box_contact_hand"].data.contact_pos_w[inspect_index, 0, 0] - base.scene.env_origins[inspect_index]
                            ).tolist(),
                            hand_contact_position_valid=bool(torch.isfinite(base.scene["box_contact_hand"].data.contact_pos_w[inspect_index, 0, 0]).all()),
                            foot_contact_force_z=base.scene["contact_forces"].data.net_forces_w[inspect_index, sensor.body_ids, 2].tolist(),
                            hand_target_error=(target - robot.data.body_pos_w[inspect_index, hand.body_ids[0]]).tolist(),
                            velocity_command=box_push.push_velocity_commands(base, hand)[inspect_index].tolist(),
                            arm_torque_limit_ratio=(robot.data.applied_torque[inspect_index, arm.joint_ids].abs() / robot.data.joint_effort_limits[inspect_index, arm.joint_ids]).tolist(),
                        )
                        if hybrid_push:
                            face, base_height, body_stable = box_push.preapproach_state(base)
                            sample.update(
                                arm_locked=bool(controller.locked[inspect_index]),
                                drive_contact=bool(controller.drive_contact[inspect_index]),
                                contact_memory_left=controller.contact_memory_left[inspect_index].item(),
                                leg_release_elapsed=controller.leg_release_elapsed[inspect_index].item(),
                                leg_release_blend=controller.leg_release_blend[inspect_index].item(),
                                velocity_integral=controller.velocity_integral[inspect_index].tolist(),
                                ik_clearance_residual=controller.clearance_residual[inspect_index].item(),
                                ik_clearance_correction=controller.clearance_correction[inspect_index].item(),
                                ik_clearance_distance=controller.clearance_distance[inspect_index].item(),
                                arm_joint_position=robot.data.joint_pos[inspect_index, controller.joint_ids].tolist(),
                                arm_joint_reference=controller.reference[inspect_index].tolist(),
                                safe_approach_complete=bool(controller.safe_approach_complete[inspect_index]),
                                safe_approach_index=int(controller.safe_approach_index[inspect_index]),
                                body_ready=bool(controller.body_ready[inspect_index]),
                                body_stable=bool(body_stable[inspect_index]),
                                body_ready_duration=controller.body_ready_duration[inspect_index].item(),
                                preapproach_elapsed=controller.preapproach_elapsed[inspect_index].item(),
                                precontact_ready=bool(controller.precontact_ready[inspect_index]),
                                precontact_joint_error=(
                                    robot.data.joint_pos[inspect_index, controller.joint_ids] - controller.precontact_posture
                                ).abs().amax().item() if controller.precontact_posture.numel() else 0.0,
                                motion_ready=bool(controller.motion_ready[inspect_index]),
                                face_local=face[inspect_index].tolist(),
                                base_height=base_height[inspect_index].item(),
                                linear_speed=torch.linalg.vector_norm(robot.data.root_lin_vel_w[inspect_index]).item(),
                                angular_speed=torch.linalg.vector_norm(robot.data.root_ang_vel_w[inspect_index]).item(),
                                contact_duration=controller.contact_duration[inspect_index].item(),
                                policy_leg_action=action_term.raw_actions[inspect_index].tolist(),
                                joint_command_leg_action=action_term.joint_commands[inspect_index, controller.leg_slots].tolist(),
                            )
                    traces[inspect_index].append(sample)
                    step_samples[inspect_index] = sample
            if video is not None and step % 2 == 0 and active[trace_index]:
                video.append_data(base.render())
            actor_input = torch.cat([observation[name] for name in observation_groups], dim=-1)
            if args.neutral_push_command:
                actor_input[:, 189:210] = actor_input.new_tensor((0.5, 0.0, 0.4, 1.0, 0.0, 0.0, 0.0)).repeat(3)
            actions = policy(actor_input)
            if deployment_actor is not None:
                deployed_actions = deployment_actor(actor_input)
                torch.testing.assert_close(deployed_actions, actions, rtol=1e-6, atol=1e-6)
                deployment_max_error = max(deployment_max_error, (deployed_actions - actions).abs().max().item())
                deployment_comparisons += int(active.sum().item())
            if arm_controller is not None:
                actions = arm_controller.apply(actions)
            if args.neutral_arm:
                actions = actions.clone()
                actions[:, 12:] = 0.0
            if step * base.step_dt < args.preparation_seconds:
                actions = torch.zeros_like(actions)
            for inspect_index, sample in step_samples.items():
                sample["applied_action"] = actions[inspect_index].tolist()
            if failure_history is not None:
                # Read existing state only: do not call push_hand_target or
                # controller.apply, which advance controller state. Target and
                # joint references belong to the previously executed command;
                # next_policy_action is the action about to enter env.step.
                action_term = base.action_manager.get_term("joint_pos")
                controller = action_term.controller
                face, _height, _stable = box_push.preapproach_state(base)
                contact_position = base.scene["box_contact_hand"].data.contact_pos_w[:, 0, 0]
                failure_history.append(
                    active,
                    elapsed_seconds=base.episode_length_buf * base.step_dt,
                    robot_position=robot.data.root_pos_w - base.scene.env_origins,
                    robot_quaternion=robot.data.root_quat_w,
                    robot_velocity=robot.data.root_lin_vel_w,
                    box_position=base.scene["box"].data.root_pos_w - base.scene.env_origins,
                    box_quaternion=base.scene["box"].data.root_quat_w,
                    hand_position=robot.data.body_pos_w[:, hand.body_ids[0]] - base.scene.env_origins,
                    hand_quaternion=robot.data.body_quat_w[:, hand.body_ids[0]],
                    hand_contact_valid=condition,
                    forbidden_box_contact=box_push.forbidden_box_contact(base),
                    hand_force=hand_force,
                    hand_contact_position=torch.nan_to_num(contact_position - base.scene.env_origins),
                    hand_contact_position_valid=torch.isfinite(contact_position).all(dim=1),
                    arm_command_position=controller.target_position - base.scene.env_origins,
                    arm_joint_position=robot.data.joint_pos[:, controller.joint_ids],
                    arm_joint_reference=controller.reference,
                    arm_joint_target=robot.data.joint_pos_target[:, controller.joint_ids],
                    arm_joint_velocity=robot.data.joint_vel[:, controller.joint_ids],
                    arm_applied_torque=robot.data.applied_torque[:, controller.joint_ids],
                    face_local=face,
                    velocity_command=box_push.push_velocity_commands(base, hand),
                    safe_approach_complete=controller.safe_approach_complete,
                    safe_approach_index=controller.safe_approach_index,
                    approach_completed=base.box_push_approached,
                    motion_ready=controller.motion_ready,
                    leg_release_blend=controller.leg_release_blend,
                    ik_clearance_distance=controller.clearance_distance,
                    next_policy_action=actions,
                )
            observation, _rewards, dones, _extras = env.step(actions)
            done = dones.bool()
            sample_motion(active & ~done)
            if arm_controller is not None:
                arm_controller.reset(done.nonzero(as_tuple=False).flatten())
            success = done & base.termination_manager.get_term("box_settled")
            for name in base.termination_manager.active_terms:
                if name not in ("box_settled", "time_out"):
                    success &= ~base.termination_manager.get_term(name)
            counted = quota.record(done, success)
            motion.reset_reference(counted, robot.data.joint_pos)
            for name in reasons:
                reasons[name] += int((counted & base.termination_manager.get_term(name)).sum().item())
            condition_duration[done] = 0.0
            if (step + 1) % 200 == 0:
                print(f"EVAL_STEP={step + 1} completed={completions.sum().item()} successes={successes.sum().item()}", flush=True)
            if not quota.active.any():
                break
    if video is not None:
        video.close()
    if climbing:
        terrain = config.scene.terrain.terrain_generator.sub_terrains["box"]
        actual_physics = {
            "box_height_range": terrain.box_height_range, "fixed_support": True,
            "approach_height": terrain.approach_height, "approach_gap": terrain.approach_gap,
            "approach_gap_range": terrain.approach_gap_range,
            "approach_length": terrain.approach_length, "approach_width": terrain.approach_width,
            "landing_length": terrain.box_length, "landing_width": terrain.box_width,
            "following_platform_height": terrain.following_platform_height,
            "following_platform_gap": terrain.following_platform_gap,
            "terrain_static_friction": config.scene.terrain.physics_material.static_friction,
            "terrain_dynamic_friction": config.scene.terrain.physics_material.dynamic_friction,
            "start_clearance": config.scene.robot.init_state.pos[2],
            "prepared_start_path": config.prepared_start_path,
            "prepared_start_phase": config.prepared_start_phase if config.prepared_start_path else None,
            "prepared_start_sha256": hashlib.sha256(Path(config.prepared_start_path).read_bytes()).hexdigest() if config.prepared_start_path else None,
        }
    else:
        box = base.scene["box"]
        actual_physics = {
            "box_mass_per_env": box.root_physx_view.get_masses().flatten().tolist(),
            "box_material_per_env": box.root_physx_view.get_material_properties().tolist(),
            "box_size": config.box_size, "fixed_support": False,
            "push_press_depth": config.push_press_depth, "push_distance": config.push_distance,
            "push_approach_distance": config.push_approach_distance,
            "push_hand_height_offset": config.push_hand_height_offset,
        }
    mdp_directory = Path(box_push.__file__).resolve().parent
    repository = Path(__file__).resolve().parents[1]
    robot_asset_directory = Path(config.scene.robot.spawn.usd_path).resolve().parent
    robot_asset_paths = sorted(robot_asset_directory.rglob("*.usd"))
    robot_asset_paths.extend(robot_asset_directory.glob("*.py"))
    if stage_mass_provenance is not None:
        stage_mass_provenance["cached_at_end"] = stage_action.mass.cpu().tolist()
        stage_mass_provenance["actual_at_end"] = base.scene["robot"].root_physx_view.get_masses().cpu().tolist()
        actual_physics["stage_mass_provenance"] = stage_mass_provenance
    actual_physics.update(
        robot_asset_sha256={str(path.relative_to(repository)): hashlib.sha256(path.read_bytes()).hexdigest() for path in robot_asset_paths},
        robot_joint_names=list(robot.joint_names),
        robot_effort_limits=robot.data.joint_effort_limits[0].tolist(),
        robot_joint_defaults=robot.data.default_joint_pos[0].tolist(),
    )
    if hybrid_push:
        controller = base.action_manager.get_term("joint_pos").controller
        actual_physics["controller_contract"] = {
            "lock_arm_on_contact": controller.lock_arm_on_contact,
            "align_hand_orientation": getattr(controller, "align_hand_orientation", False),
            "hand_pitch": getattr(config.actions.joint_pos, "hand_pitch", 0.0),
            "approach_distance": config.push_approach_distance,
            "hand_height_offset": config.push_hand_height_offset,
            "press_depth": config.push_press_depth, "control_dt": base.step_dt,
            "precontact_heights": controller.precontact_heights.tolist(),
            "ik_clearance_minimum": controller.clearance_minimum,
            "ik_orientation_weight": controller.orientation_weight,
            "ik_height_weight": controller.height_weight,
            "ik_joint_limit_solve": controller.joint_limit_solve,
            "goal_hold_pose": controller.goal_hold_pose,
            "goal_release_distance": controller.goal_release_distance,
            "goal_brake_gain": getattr(config, "push_goal_brake_gain", 0.0),
            "press_on_legal_contact": getattr(config, "push_press_on_legal_contact", False),
            "control_stop_distance": getattr(config, "push_stop_distance", 0.10),
            "leg_release_on_contact": controller.leg_release_on_contact,
            "contact_memory_s": controller.contact_memory_s,
            "leg_release_ramp_s": controller.leg_release_ramp_s,
            "leg_contact_ramp_s": controller.leg_contact_ramp_s,
            "forward_command_gain": getattr(config, "push_forward_command_gain", 1.0),
            "contact_gap_slowdown_start": getattr(config, "push_contact_gap_slowdown_start", 0.0),
            "target_maximum_reach": getattr(config, "push_target_maximum_reach", 0.0),
            "velocity_feedback_gain": getattr(config, "push_velocity_feedback_gain", 0.0),
            "velocity_integral_gain": controller.velocity_integral_gain,
            "body_first": controller.body_first,
            "preapproach_base_gap": getattr(config, "push_preapproach_base_gap", None) if controller.body_first else None,
            "ik_clearance_geometry": "body_centers_linearized" if controller.clearance_minimum is not None else None,
        }
    control_files = ("box_climb.py", "box_rewards.py", "box_terrain.py") if climbing else ("box_push.py", "box_push_control.py", "box_rewards.py")
    if "Climb-Crawl" in args.task or "Climb-Stages" in args.task:
        control_files += ("box_climb_crawl.py", "crawl_gait.py")
        actual_physics["crawl_contract"] = {name: getattr(config.actions.joint_pos, name) for name in (
            "transfer_s", "swing_s", "settle_s", "stride", "foot_clearance", "leg_rate", "arm_rate", "leg_acceleration", "arm_acceleration", "foot_tracking_length_scale", "lift_tolerance", "landing_xy_tolerance")}
    if "Climb-Stages" in args.task:
        control_files += ("box_climb_stages.py", "climb_stage_math.py")
        if config.actions.joint_pos.guidance_enabled:
            control_files += ("climb_guidance.py", "climb_leg_kinematics.py", "climb_body_clearance.py")
        actual_physics["climb_guidance"] = {
            "enabled": config.actions.joint_pos.guidance_enabled,
            "residual_scale": config.actions.joint_pos.guidance_residual_scale,
            "reference_joint_ids": list(base.action_manager.get_term("joint_pos")._joint_ids),
            "body_gain": config.actions.joint_pos.guidance_body_gain,
            "body_damping": config.actions.joint_pos.guidance_body_damping,
            "loaded_start": config.actions.joint_pos.guidance_loaded_start,
            "forward_lift": config.actions.joint_pos.guidance_forward_lift,
            "body_clearance": config.actions.joint_pos.guidance_body_clearance,
            "force_balance": config.actions.joint_pos.guidance_force_balance,
            "horizontal_balance": config.actions.joint_pos.guidance_horizontal_balance,
            "preunload": config.actions.joint_pos.guidance_preunload,
            "landing_contact": config.actions.joint_pos.guidance_landing_contact,
            "mixed_height": config.actions.joint_pos.guidance_mixed_height,
            "support_feedback": config.actions.joint_pos.guidance_support_feedback,
            "support_plane": config.actions.joint_pos.guidance_support_plane,
            "plane_fraction": config.actions.joint_pos.guidance_plane_fraction,
            "feasible_pose": config.actions.joint_pos.guidance_feasible_pose,
            "body_collision": config.actions.joint_pos.guidance_body_collision,
            "independent_height": config.actions.joint_pos.guidance_independent_height,
            "leg_collision": config.actions.joint_pos.guidance_leg_collision,
            "primitive_collision": config.actions.joint_pos.guidance_primitive_collision,
            "load_preview": config.actions.joint_pos.guidance_load_preview,
            "swing_preview": config.actions.joint_pos.guidance_swing_preview,
            "swing_transfer": config.actions.joint_pos.guidance_swing_transfer,
            "last_pose_search": config.actions.joint_pos.guidance_last_pose_search,
            "edge_pose_search": config.actions.joint_pos.guidance_edge_pose_search,
            "pose_angle_coverage": config.actions.joint_pos.guidance_pose_angle_coverage,
            "last_rear_swing_inset": config.actions.joint_pos.last_rear_swing_inset,
            "front_raise_height": config.actions.joint_pos.front_raise_height,
            "rotate_com": config.actions.joint_pos.guidance_rotate_com,
            "platform_pose": config.actions.joint_pos.guidance_platform_pose,
            "platform_hold": config.actions.joint_pos.guidance_platform_hold,
            "platform_level": config.actions.joint_pos.guidance_platform_level,
            "platform_hold_tracking": config.actions.joint_pos.guidance_platform_hold_tracking,
            "platform_hold_tracking_max_extra": config.actions.joint_pos.guidance_platform_hold_tracking_max_extra,
            "platform_front_extension": config.actions.joint_pos.platform_front_extension,
            "platform_front_first": config.actions.joint_pos.platform_front_first,
            "platform_final_adjust": config.actions.joint_pos.platform_final_adjust,
            "front_force_trim": config.actions.joint_pos.guidance_front_force_trim,
            "front_followup_force_trim": config.actions.joint_pos.guidance_front_followup_force_trim,
            "platform_extension_force_trim": config.actions.joint_pos.guidance_platform_extension_force_trim,
            "platform_extension_tracking": config.actions.joint_pos.guidance_platform_extension_tracking,
            "platform_settled_recovery": config.actions.joint_pos.guidance_platform_settled_recovery,
            "platform_final_recovery_rise": config.actions.joint_pos.guidance_platform_final_recovery_rise,
            "front_followup_preview": config.actions.joint_pos.guidance_front_followup_preview,
            "single_front_pose": config.actions.joint_pos.guidance_single_front_pose,
            "retain_infeasible_reference": config.actions.joint_pos.guidance_retain_infeasible_reference,
            "refine_height": config.actions.joint_pos.guidance_refine_height,
            "endpoint_leg_reserve": config.actions.joint_pos.guidance_endpoint_leg_reserve,
            "endpoint_body_reserve": config.actions.joint_pos.guidance_endpoint_body_reserve,
            "platform_load_reserve": config.actions.joint_pos.guidance_platform_load_reserve,
            "front_ascent_pose": config.actions.joint_pos.guidance_front_ascent_pose,
            "platform_support_path": config.actions.joint_pos.guidance_platform_support_path,
            "platform_support_recovery": config.actions.joint_pos.guidance_platform_support_recovery,
            "platform_swing": config.actions.joint_pos.guidance_platform_swing,
            "rotate_com_scope": ("last ground rear ascent, three platform supports and four contacts; also post-hold front extension" if config.actions.joint_pos.platform_front_extension is not None else "last ground rear ascent, three platform supports and four contacts") if config.actions.joint_pos.guidance_rotate_com else None,
            "leg_collision_scope": ("USD primitive support radii;21 nominal path samples;5mm separation;full/half/quarter XY transfer" if config.actions.joint_pos.guidance_primitive_collision else "USD hip/thigh/calf bounding boxes;21 nominal path samples;5mm separation;full/half/quarter XY transfer") if config.actions.joint_pos.guidance_leg_collision else None,
            "body_collision_scope": "base USD bounds,21 path samples,1cm gap; estimated load bias; not dynamics proof" if config.actions.joint_pos.guidance_body_collision else None,
            "rear_ground_stride": config.actions.joint_pos.rear_ground_stride,
            "front_followup": config.actions.joint_pos.front_followup,
            "front_followup_target": config.actions.joint_pos.front_followup_target,
            "rear_ascent_target": config.actions.joint_pos.rear_ascent_target,
            "rear_edge_prep": config.actions.joint_pos.rear_edge_prep,
        }
        actual_physics["climb_stage_bank_sha256"] = hashlib.sha256(args.climb_stage_bank.read_bytes()).hexdigest() if args.climb_stage_bank else None
        actual_physics["climb_start_scope"] = "training_curriculum_diagnostic" if args.climb_stage_bank else "original_start"
    if climbing and config.prepared_start_path:
        control_files += ("climb_start_states.py",)
    if args.arm_ik:
        control_files += ("box_push_ik.py",)
    if hybrid_push:
        control_files += ("box_push_ik.py", "box_push_actions.py")
    front_swing_inputs = {}
    front_swing_inputs_excluded = []
    platform_pose_inputs = {}
    platform_level_inputs = {}
    platform_final_inputs = {}
    platform_preextension_inputs = {}
    platform_final_plan_inputs = {}
    front_followup_pose_inputs = {}
    platform_inputs_excluded = {}
    if args.climb_guidance_pose_fixtures:
        # Other environments keep stepping after an environment's quota ends.
        # Its later collector entries are not evidence from the recorded episode.
        terminal_times = {state["env_id"]: state["elapsed_seconds"] for state in terminal_states}
        for key, record in base.action_manager.get_term("joint_pos").guidance.front_swing_inputs.items():
            if record["elapsed_s"] <= terminal_times.get(record["env_id"], float("inf")) + 1e-6:
                front_swing_inputs[key] = record
            else:
                front_swing_inputs_excluded.append(key)
        guidance = base.action_manager.get_term("joint_pos").guidance
        for label, source, target in (
                ("pose", guidance.platform_pose_inputs, platform_pose_inputs),
                ("level", guidance.platform_level_inputs, platform_level_inputs),
                ("final", guidance.platform_final_inputs, platform_final_inputs),
                ("preextension", guidance.platform_preextension_inputs, platform_preextension_inputs),
                ("final_plan", guidance.platform_final_plan_inputs, platform_final_plan_inputs),
                ("front_followup_pose", guidance.front_followup_pose_inputs, front_followup_pose_inputs)):
            excluded = {}
            for key, records in source.items():
                target[key] = [record for record in records
                    if record["elapsed_s"] <= terminal_times.get(record["env_id"], float("inf")) + 1e-6]
                if len(target[key]) != len(records):
                    excluded[key] = len(records)-len(target[key])
            platform_inputs_excluded[label] = excluded
    result = {
        "schema_version": 4, "episodes_per_env": args.episodes_per_env,
        "neutral_arm_diagnostic": args.neutral_arm,
        "neutral_push_command_diagnostic": args.neutral_push_command,
        "preparation_seconds": args.preparation_seconds,
        "observation_noise_diagnostic": args.observation_noise,
        "collision_variant_diagnostic": collision_variant is not None,
        "collision_variant": collision_variant,
        "base_start_diagnostic": args.base_start_x is not None,
        "neutral_legs_diagnostic": args.neutral_legs,
        "base_start_position": config.scene.robot.init_state.pos,
        "terminal_states": terminal_states,
        "termination_flag_names": list(base.termination_manager.active_terms),
        "requested_episodes": args.num_envs * args.episodes_per_env,
        "incomplete_episodes": int((args.episodes_per_env - completions).sum().item()),
        "checkpoint_sha256": hashlib.sha256(args.checkpoint.read_bytes()).hexdigest() if args.checkpoint else None,
        "actor_policy": str(args.actor_policy) if args.actor_policy else None,
        "actor_policy_sha256": hashlib.sha256(args.actor_policy.read_bytes()).hexdigest() if args.actor_policy else None,
        "locomotion_policy": str(args.locomotion_policy) if args.locomotion_policy else None,
        "locomotion_policy_sha256": hashlib.sha256(args.locomotion_policy.read_bytes()).hexdigest() if args.locomotion_policy else None,
        "evaluation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "deployment_actor_sha256": hashlib.sha256(args.deployment_actor.read_bytes()).hexdigest() if args.deployment_actor else None,
        "deployment_actor_max_abs_error": deployment_max_error if deployment_actor is not None else None,
        "deployment_actor_comparisons": deployment_comparisons,
        "control_sha256": {name: hashlib.sha256((mdp_directory / name).read_bytes()).hexdigest() for name in control_files},
        "actual_physics": actual_physics, "executed_steps": step + 1,
        "episode_length_s": config.episode_length_s,
        "arm_controller": "trained_legs_with_ik_arm" if hybrid_push else "differential_ik_gravity_diagnostic" if args.arm_ik else "learned_policy",
        "stand_until_arm_ready": args.locomotion_policy is not None or hybrid_push,
        "lock_arm_on_contact": base.action_manager.get_term("joint_pos").controller.lock_arm_on_contact if hybrid_push else args.locomotion_policy is not None,
        "climb_ground_pose_inputs": getattr(base.action_manager.get_term("joint_pos").guidance, "ground_pose_inputs", {}),
        "climb_platform_search_inputs": getattr(base.action_manager.get_term("joint_pos").guidance, "platform_search_inputs", {}),
        "climb_final_search_inputs": getattr(base.action_manager.get_term("joint_pos").guidance, "final_search_inputs", {}),
        "climb_last_rear_pose_inputs": getattr(base.action_manager.get_term("joint_pos").guidance, "last_rear_pose_inputs", {}),
        "climb_rear_prep_inputs": getattr(base.action_manager.get_term("joint_pos").guidance, "rear_prep_inputs", {}),
        "climb_failed_pose_inputs": base.action_manager.get_term("joint_pos").guidance.failed_pose_inputs if args.climb_guidance_pose_fixtures else {},
        "climb_platform_pose_inputs": platform_pose_inputs,
        "climb_platform_level_inputs": platform_level_inputs,
        "climb_platform_final_inputs": platform_final_inputs,
        "climb_platform_preextension_inputs": platform_preextension_inputs,
        "climb_platform_final_plan_inputs": platform_final_plan_inputs,
        "climb_front_followup_pose_inputs": front_followup_pose_inputs,
        "climb_platform_inputs_excluded_after_terminal": platform_inputs_excluded,
        "climb_front_ascent_inputs": {key:record for key,record in base.action_manager.get_term("joint_pos").guidance.front_ascent_inputs.items()
            if record["elapsed_s"] <= terminal_times.get(record["env_id"], float("inf")) + 1e-6} if args.climb_guidance_pose_fixtures else {},
        "climb_front_swing_inputs": front_swing_inputs,
        "climb_front_swing_inputs_excluded_after_terminal": front_swing_inputs_excluded,
        "inspect_dense_after_s": args.inspect_dense_after_s,
        "inspect_extra_env_indices": args.inspect_extra_env_indices,
        **{f"trace_env{i}": values for i, values in traces.items()},
        "inspect_env_index": trace_index, "video_path": str(args.video_path) if args.video_path else None,
        "video_camera_eye": camera_eye if args.video_path else None,
        "video_camera_target": camera_target if args.video_path else None,
        "video_isolate_environment": args.video_isolate_environment,
        "failure_history_steps": args.failure_history_steps,
        "failure_history_step_dt": float(base.step_dt),
        "failure_history_arm_joint_names": [robot.joint_names[i] for i in base.action_manager.get_term("joint_pos").controller.joint_ids] if failure_history is not None else [],
        "failure_histories": failure_histories,
        "failure_history_sample_phase": "pre_env_step; controller targets describe previous command; next_policy_action is the next action; terminal_state_index points to the post-physics pre-reset state",
        "evaluation_helpers_sha256": {"box_evaluation_metrics.py": hashlib.sha256((Path(__file__).parent / "box_evaluation_metrics.py").read_bytes()).hexdigest()},
        "climb_gait_quality": gait_quality.report() if gait_quality is not None else None,
        "platform_stage_diagnostic": {
            "scope": "Per-environment maximum continuous duration. Stage only; excludes goal-center requirement, not original task success or actuator acceptance.",
            "four_supported_feet_max_seconds": maximum_platform_duration[:, 0].tolist(),
            "four_supported_feet_and_original_motion_posture_max_seconds": maximum_platform_duration[:, 1].tolist(),
            "four_supported_feet_at_least_1s_envs": int((maximum_platform_duration[:, 0] >= 1.).sum().item()),
            "original_motion_posture_at_least_1s_envs": int((maximum_platform_duration[:, 1] >= 1.).sum().item()),
        } if climbing else None,
        "task": args.task, "checkpoint": str(args.checkpoint) if args.checkpoint else None, "seed": args.seed,
        "num_envs": args.num_envs, "steps": args.steps, "box_height": args.box_height,
        "box_mass": args.box_mass, "box_friction": args.box_friction,
        "completed_episodes": int(completions.sum().item()), "successful_episodes": int(successes.sum().item()),
        "per_env_completions": completions.tolist(), "per_env_successes": successes.tolist(),
        "termination_reasons": reasons, "max_forward_per_env": maximum_forward.tolist(),
        "min_base_height_per_env": minimum_base_height.tolist(), "max_tilt_radians_per_env": maximum_tilt.tolist(),
        "max_standing_seconds" if climbing else "max_hand_contact_seconds": maximum_condition.tolist(),
        "max_supported_feet": maximum_support.tolist() if climbing else None,
        "max_torque_limit_ratio": maximum_torque_ratio,
        "joint_motion": motion.summary(),
        "push_contact_steps": push_contact_steps.tolist() if not climbing else None,
        "unclassified_hand_contact_steps": unclassified_hand_contact_steps.tolist() if not climbing else None,
        "max_unclassified_hand_force": maximum_unclassified_hand_force.tolist() if not climbing else None,
        "mean_hand_force_on_contact": (push_force_sum / push_contact_steps.clamp_min(1.0)).tolist() if not climbing else None,
        "max_hand_force": maximum_push_force.tolist() if not climbing else None,
        "joint_names": robot.joint_names, "body_names": robot.body_names,
        "contact_body_names": list(base.scene["contact_forces"].body_names),
        "max_abs_joint_velocity": maximum_joint_velocity.tolist(),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    # Save the complete outcome and quality summary before large dense traces.
    # This changes serialization only, after the physical evaluation has ended.
    if args.output_json.exists():
        raise FileExistsError(args.output_json)
    summary_keys = (
        "schema_version", "terminal_states", "termination_flag_names",
        "requested_episodes", "incomplete_episodes", "completed_episodes", "successful_episodes",
        "per_env_completions", "per_env_successes", "termination_reasons",
        "task", "seed", "num_envs", "episode_length_s", "actual_physics",
        "control_sha256", "actor_policy_sha256", "evaluation_sha256", "evaluation_helpers_sha256",
        "climb_gait_quality", "joint_motion", "max_supported_feet", "platform_stage_diagnostic",
        "max_torque_limit_ratio", "joint_names", "body_names", "executed_steps")
    outcome = {key: result[key] for key in summary_keys if key in result}
    outcome["dense_report_pending"] = True
    with args.output_json.with_suffix(".outcomes.json").open("x", encoding="utf-8") as stream:
        json.dump(outcome, stream, separators=(",", ":"), allow_nan=False)
    partial = args.output_json.with_suffix(".json.partial")
    with partial.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, separators=(",", ":"), allow_nan=False)
    partial.replace(args.output_json)
    if args.summary_log:
        summary = {key: result[key] for key in (
            "task", "seed", "num_envs", "completed_episodes", "successful_episodes",
            "incomplete_episodes", "termination_reasons", "evaluation_sha256",
            "actor_policy_sha256", "control_sha256")}
        summary["output_json"] = str(args.output_json.resolve())
        print("BOX_SKILL_EVALUATION_SUMMARY=" + json.dumps(summary, allow_nan=False), flush=True)
    else:
        print("BOX_SKILL_EVALUATION=" + json.dumps(result, allow_nan=False))
    env.close()


try:
    main()
except Exception:
    traceback.print_exc()
    try:
        launcher.app.close()
    finally:
        raise SystemExit(1)
else:
    launcher.app.close()
