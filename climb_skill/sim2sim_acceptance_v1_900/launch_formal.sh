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
cd /mnt/miaojigui/zyh/climb_skill/sim2sim_acceptance_v1_900/eval-frozen-v3
/mnt/miaojigui/conda/envs/go2-piper/bin/python ../run_remote_formal.py > ../formal-v3-launch.log 2>&1
