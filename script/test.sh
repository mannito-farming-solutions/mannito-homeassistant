#!/bin/sh
# Runs lint, types and tests in a Linux container (Home Assistant does not run on Windows).
# Usage from the repository root: sh script/test.sh [pytest arguments]
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W 2>/dev/null || pwd):/src" -v mannito-ha-venv:/venv -w /src python:3.14-slim sh -c "
  pip install -q uv 2>/dev/null
  [ -x /venv/bin/python ] || uv venv -q /venv
  uv pip install -q --python /venv/bin/python -r requirements_test.txt
  /venv/bin/python -m pytest -p no:cacheprovider $*
"
