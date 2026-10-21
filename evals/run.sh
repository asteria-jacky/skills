#!/usr/bin/env bash
# Run the review eval suite. See evals/README.md.
#
#   evals/run.sh quick [case...]   1 try per case
#   evals/run.sh full  [case...]   3 tries per case (empty-diff: 1)
#
# With no case names, every case runs. Each case runs as its own
# `claude plugin eval` call, in parallel, with the threshold that
# threshold_for gives its tag: the one place the bars are set.
# Env: EVAL_MODEL (default sonnet), EVAL_MAX_COST_USD per case (default 3),
#      EVAL_KEEP_TEMP=1 to keep each try's workspace and trace (for token
#      counts and for reading the report a try wrote).
set -uo pipefail

mode=${1:-}; shift || true
case "$mode" in
  quick) runs_flag=(--runs 1) ;;
  full) runs_flag=() ;;            # each case's own `runs`
  *) echo "usage: evals/run.sh quick|full [case...]" >&2; exit 64 ;;
esac

root=$(cd "$(dirname "$0")/.." && pwd)
evals="$root/evals"
model=${EVAL_MODEL:-sonnet}
max_cost_usd=${EVAL_MAX_COST_USD:-3}
out="$evals/results/$(date +%Y%m%d-%H%M%S)-$mode"
mkdir -p "$out"
keep_temp_flag=(); [ "${EVAL_KEEP_TEMP:-}" = 1 ] && keep_temp_flag=(--keep-temp)

if [ $# -eq 0 ]; then
  set -- $(cd "$evals" && for d in */case.yaml; do echo "${d%/case.yaml}"; done)
fi

# The bar per tag: clean and failure cases must be right every try;
# verdict cases right in 2 of 3 tries.
threshold_for() {
  local tags; tags=$(grep '^tags:' "$evals/$1/case.yaml")
  case "$tags" in
    *clean*|*failure*) echo 1.0 ;;
    *) echo 0.66 ;;
  esac
}

# What a review may do in the eval sandbox: write its report folder and move
# log, and run the read-only git commands its skills' allowed-tools list.
grants=(
  "Write(review/**)" "Edit(review/**)"
  "Write(move-log/**)" "Edit(move-log/**)"
  "Bash(git diff *)" "Bash(git log *)" "Bash(git rev-parse *)"
  "Bash(git merge-base *)" "Bash(git show *)"
)

pids=()
for c in "$@"; do
  [ -f "$evals/$c/case.yaml" ] || { echo "no case: $c" >&2; exit 64; }
  ( cd "$root" && claude plugin eval . --case "$c" "${runs_flag[@]}" \
      --ablation none --scaffold --trust-plugin --no-publish "${keep_temp_flag[@]}" \
      --allow-tools "${grants[@]}" \
      --model "$model" --max-cost-usd "$max_cost_usd" --threshold "$(threshold_for "$c")" \
      --output-dir "$out/$c" --json "$out/$c.json" >"$out/$c.log" 2>&1
    echo $? >"$out/$c.exit" ) &
  pids+=($!)
done
wait "${pids[@]}"

python3 - "$out" "$@" <<'PY'
import json, os, sys
out, cases = sys.argv[1], sys.argv[2:]


def tokens(trace):
    """All tokens of one try, sub-agents included, from the trace's result event."""
    total = None
    try:
        with open(trace) as fh:
            for line in fh:
                m = json.loads(line)
                if m.get("type") == "result" and m.get("modelUsage"):
                    total = sum(u.get(k, 0) for u in m["modelUsage"].values()
                                for k in ("inputTokens", "outputTokens",
                                          "cacheReadInputTokens", "cacheCreationInputTokens"))
    except (OSError, ValueError):
        pass
    return total


any_case_failed = False
for c in cases:
    with open(os.path.join(out, c + ".exit")) as fh:
        code = fh.read().strip()
    any_case_failed |= code != "0"
    try:
        with open(os.path.join(out, c + ".json")) as fh:
            case = json.load(fh)["cases"][0]
    except Exception as e:
        print(f"{c:19} no result ({e.__class__.__name__}), exit {code}; see {c}.log")
        continue
    print(f"{c:19} score {case['aggregates']['score']:.2f}  exit {code}")
    for i, run in enumerate(case["arms"]["with"]):
        failed = [g["name"] for g in run["graders"] if not g["passed"]]
        tok = tokens(run.get("tracePath") or "")
        print(f"  try {i + 1}: ${run['costUsd']:.2f}  {run['durationSeconds']}s  {run['turns']} turns"
              f"  tokens {tok if tok is not None else '?'}  failed: {', '.join(failed) or '-'}"
              f"{'  error: ' + str(run['error']) if run.get('error') else ''}")
        if run.get("tracePath"):
            print(f"         trace {run['tracePath']}")
print("results:", out)
sys.exit(1 if any_case_failed else 0)
PY
