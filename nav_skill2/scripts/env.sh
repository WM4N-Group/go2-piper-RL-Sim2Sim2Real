# source本文件后可以直接import外部包；train.py/play.py已自动设置包路径。
NAV2_PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$NAV2_PROJECT/source/nav_skill2${PYTHONPATH:+:$PYTHONPATH}"
export ROBOT_USD="${ROBOT_USD:-$NAV2_PROJECT/../asset/go2_piper/go2_piper.usd}"
