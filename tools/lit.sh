#!/usr/bin/env bash
# Light a spark, or put it back.
#   bash tools/lit.sh identity-fusion 14    -> lit, comments on issue 14
#   bash tools/lit.sh identity-fusion off   -> back to a spark
#
# Unlighting is lossless. Extra reads and the slate note stay in the record;
# the spark view just stops showing them.
set -euo pipefail
cd "$(dirname "$0")/.."
id="${1:?usage: lit.sh <node-id> <issue-number|off>}"
arg="${2:?usage: lit.sh <node-id> <issue-number|off>}"
f="nodes/$id.json"
[ -f "$f" ] || { echo "no such node: $f"; exit 1; }

python3 - "$f" "$arg" << 'PY'
import json, sys, pathlib
f, arg = pathlib.Path(sys.argv[1]), sys.argv[2]
n = json.loads(f.read_text())
if arg == "off":
    n.pop("lit", None); n.pop("issue", None)
    print(f"{n['id']}: back to a spark ({len(n.get('reads', []))} read(s) held)")
else:
    n["lit"] = True; n["issue"] = int(arg)
    print(f"{n['id']}: lit, comments on issue {arg}")
f.write_text(json.dumps(n, indent=2) + "\n")
PY
node build.mjs
