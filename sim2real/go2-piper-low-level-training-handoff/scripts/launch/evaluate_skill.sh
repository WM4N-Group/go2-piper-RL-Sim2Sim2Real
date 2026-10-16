#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "usage: $0 {push|climb} OUTPUT_JSON [evaluate_box_skills.py arguments]" >&2
    exit 2
fi

skill="$1"
output_json="$2"
shift 2
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
: "${ISAAC_PYTHON:?Set ISAAC_PYTHON to the Isaac Lab Python launcher.}"

case "$skill" in
    push)
        task="GO2-PIPER-Box-Push-Hybrid-Play"
        checkpoint="$root/checkpoints/push/model_599.pt"
        ;;
    climb)
        task="GO2-PIPER-Box-Climb-Play"
        checkpoint="$root/checkpoints/climb/model_200.pt"
        ;;
    *)
        echo "unknown skill: $skill" >&2
        exit 2
        ;;
esac

cd "$root"
export PYTHONPATH="$root/source/LeggedManip_Lab${PYTHONPATH:+:$PYTHONPATH}"
exec "$ISAAC_PYTHON" "$root/scripts/evaluate_box_skills.py" --headless --task "$task" --checkpoint "$checkpoint" --num_envs 32 --episodes-per-env 1 --output-json "$output_json" "$@"