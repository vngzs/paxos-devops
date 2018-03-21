#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON="$(which 'python3' 2> /dev/null)"

if [[ -z "${PYTHON// }" ]]; then
    echo 2>&1 "need python3"
    exit 1
fi

AIOHTTP_TEST="${SCRIPT_DIR}/aiohttp-test.py"

"${PYTHON}" -c 'import aiohttp' &> /dev/null
if [[ ! $? -eq 0 ]]; then
    echo 2>&1 "need to install aiohttp for python"
    exit 1
fi

"${PYTHON}" -c 'import sys; vi=sys.version_info; \
    (vi[0] == 3 and vi[1] >= 4) or sys.exit(1)' &> /dev/null
if [[ ! $? -eq 0 ]]; then
    echo 2>&1 "need python > 3.4"
    exit 1
fi

exec "${AIOHTTP_TEST}" $@
exit $?
