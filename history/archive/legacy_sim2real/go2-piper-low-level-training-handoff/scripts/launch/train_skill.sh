#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "usage: $0 {push|climb} [train.py arguments]" >&2
    exit 2
fi

skill="$1"
shift
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
: "${ISAAC_PYTHON:?Set ISAAC_PYTHON to the Isaac Lab Python launcher.}"

case "$skill" in
    push)
        task="GO2-PIPER-Box-Push-Hybrid"
        checkpoint="$root/checkpoints/push/model_599.pt"
        ;;
    climb)
        task="GO2-PIPER-Box-Climb"
        checkpoint="$root/checkpoints/climb/model_200.pt"
        ;;
    *)
        echo "unknown skill: $skill" >&2
        exit 2
        ;;
esac

cd "$root"
export PYTHONPATH="$root/source/LeggedManip_Lab${PYTHONPATH:+:$PYTHONPATH}"
exec "$ISAAC_PYTHON" "$root/scripts/rsl_rl/train.py" --headless --task "$task" --init_checkpoint "$checkpoint" "$@"