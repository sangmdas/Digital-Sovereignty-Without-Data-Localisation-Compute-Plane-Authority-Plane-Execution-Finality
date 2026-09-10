#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python3 -m compileall -q src/sovereignty_ref
pytest tests/sovereignty -q
pytest --cov=src/finality_ref --cov=src/sovereignty_ref --cov-report=term-missing -q
printf 'Digital-sovereignty reference checks passed.\n'
