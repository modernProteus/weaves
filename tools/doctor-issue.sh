#!/usr/bin/env bash
# Why didn't that issue become a spark?  bash tools/doctor-issue.sh [issue-number]
set -uo pipefail
cd "$(dirname "$0")/.."

N="${1:-}"
if [ -z "$N" ]; then
  echo "── recent issues ──────────────────────────────────"
  gh issue list --state all --limit 5 \
    --json number,title,labels,state \
    --template '{{range .}}  #{{.number}}  {{.state}}  [{{range .labels}}{{.name}} {{end}}]  {{.title}}
{{end}}'
  echo
  echo "Pick one:  bash tools/doctor-issue.sh <number>"
  exit 0
fi

echo "── issue #$N ──────────────────────────────────────"
gh issue view "$N" --json number,title,state,labels,body \
  --template 'state    {{.state}}
labels   {{range .labels}}{{.name}} {{end}}
title    {{.title}}
'
echo
echo "fields the parser will see:"
gh issue view "$N" --json body -q .body \
  | awk '/^### /{h=substr($0,5); getline; getline; printf "  %-34s %s\n", h, substr($0,1,44)}'

echo
echo "── did the bot run ────────────────────────────────"
gh issue view "$N" --json comments \
  -q '.comments[] | "  " + (.body | split("\n")[0])' 2>/dev/null \
  | head -5 || echo "  no comments — workflow never ran, or ran and failed"

echo
echo "── workflow runs ──────────────────────────────────"
gh run list --limit 4 \
  --json databaseId,name,conclusion,createdAt \
  --template '{{range .}}  {{.databaseId}}  {{printf "%-22s" .name}}  {{.conclusion}}
{{end}}'

echo
echo "── trigger conditions ─────────────────────────────"
printf "  %-30s %s\n" "workflow file present" \
  "$([ -f .github/workflows/from-issue.yml ] && echo yes || echo NO)"
printf "  %-30s %s\n" "fires on label" \
  "$(grep -o "labels\.\*\.name, '[a-z]*'" .github/workflows/from-issue.yml 2>/dev/null | sed "s/.*'\(.*\)'/\1/")"
printf "  %-30s %s\n" "template applies labels" \
  "$(grep -o 'labels: \[.*\]' .github/ISSUE_TEMPLATE/spark.yml 2>/dev/null)"
printf "  %-30s %s\n" "commits to" \
  "$(grep -o 'git add [a-z/]*' .github/workflows/from-issue.yml 2>/dev/null)"

echo
echo "── local ──────────────────────────────────────────"
git pull -q 2>/dev/null
printf "  nodes/: %s\n" "$(ls nodes/*.json 2>/dev/null | wc -l | tr -d ' ') records"
ls -t nodes/*.json 2>/dev/null | head -3 | sed 's|^|    |'
