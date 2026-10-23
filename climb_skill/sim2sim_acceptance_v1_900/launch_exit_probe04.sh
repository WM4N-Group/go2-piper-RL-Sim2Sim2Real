#!/usr/bin/env bash
set -euo pipefail
export CONDA_PREFIX=/mnt/miaojigui/conda/envs/go2-piper
export LD_PRELOAD=/mnt/miaojigui/conda/envs/go2-piper/lib/libstdc++.so.6
export OMNI_KIT_ACCEPT_EULA=YES
export CLIMB_ROBOT_USD=/mnt/miaojigui/zyh/asset/go2_piper/go2_piper.usd
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export CUDA_VISIBLE_DEVICES=0
cd /mnt/miaojigui/zyh/climb_skill/sim2sim_acceptance_v1_900
/mnt/miaojigui/conda/envs/go2-piper/bin/python isaac_reference.py --headless --device cuda:0 --checkpoint /mnt/miaojigui/zyh/climb_skill/outputs/V1/train-20261019-110256-00f00wtw/model_900.pt --snapshot /mnt/miaojigui/zyh/climb_skill/outputs/V1/train-20261019-110256-00f00wtw/source --output exit-probe-04 --exit-control --nominal --episodes 1 --num-envs 1 --seed 75001 > exit-probe-04.log 2>&1
