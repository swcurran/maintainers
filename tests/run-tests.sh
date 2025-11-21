#!/bin/bash
set -e

cd "$(dirname "$0")"   # enter tests folder

GEN="../generate-maintainers.py"
REPO="test-repo"
PROJECT="TestProject"

echo "=== TEST 1: ORG ONLY (no project override) ==="
python3 $GEN \
  --repo "$REPO" \
  --project "$PROJECT" \
  --config "org-config.yaml" \
  --no-fetch > out-org.md
echo "DONE: out-org.md"


echo "=== TEST 2: PROJECT OVERRIDES ORG ==="
python3 $GEN \
  --repo "$REPO" \
  --project "$PROJECT" \
  --config "project-config.yaml" \
  --no-fetch > out-project.md
echo "DONE: out-project.md"


echo "=== TEST 3: REPO OVERRIDES PROJECT + ORG ==="
python3 $GEN \
  --repo "$REPO" \
  --project "$PROJECT" \
  --config "repo-config.yaml" \
  --no-fetch > out-repo.md
echo "DONE: out-repo.md"


echo "=== CHECKING EXPECTED OVERRIDE BEHAVIOR ==="

echo "-- Comparing org vs project (should differ in BEFORE only)"
if diff -u out-org.md out-project.md | grep '^'; then
  echo "Expected differences: OK"
else
  echo "ERROR: org and project outputs are identical (should differ)"
  exit 1
fi

echo "-- Comparing project vs repo (repo overrides before & after)"
if diff -u out-project.md out-repo.md | grep '^'; then
  echo "Expected differences: OK"
else
  echo "ERROR: project and repo outputs are identical (should differ)"
  exit 1
fi

echo
echo "=== ALL TESTS PASSED ==="
echo
echo "Generated files:"
ls -1 out-*.md