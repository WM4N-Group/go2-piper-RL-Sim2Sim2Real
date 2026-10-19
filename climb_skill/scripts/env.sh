# 必须 source 本文件；固定导入同一个可切换项目，避免旧 editable 安装指向另一个副本。
CLIMB_PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$CLIMB_PROJECT_ROOT/source/climb_skill${PYTHONPATH:+:$PYTHONPATH}"
export CLIMB_PROJECT_ROOT
# 输出目录由当前 VERSION.json 动态决定，切换后不沿用旧版本目录。
unset CLIMB_OUTPUT_ROOT

export CLIMB_AMP_DATASET="${CLIMB_AMP_DATASET:-$CLIMB_PROJECT_ROOT/data/amp_pairs.json}"
