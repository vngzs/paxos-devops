#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CERT="${SCRIPT_DIR}/../localhost.crt"

docker-compose down
docker-compose up --build -d && \
    "${SCRIPT_DIR}/ensure_up.sh" && \
    ("${SCRIPT_DIR}/../devops-test-script/test.py" -c "${CERT}" || \
        ("${SCRIPT_DIR}/clean.py" 2> /dev/null && \
        "${SCRIPT_DIR}/../devops-test-script/test.py" -c "${CERT}"); \
    "${SCRIPT_DIR}/clean.py" &> /dev/null)

