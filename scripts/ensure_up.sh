#!/usr/bin/env bash

unalias -a
shopt -s expand_aliases

alias showname='debug -n "${FUNCNAME[0]} ... "'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

OPENSSL="$(which openssl)"
PYTHON2="$(which python2)"
NMAP_NETCAT="$(ncat --version 2>&1 1>/dev/null | grep 'nmap' &>/dev/null && which ncat)"


CHECK_PYSCRIPT="${SCRIPT_DIR}/ensure_up.py"

usage() {
    cat << EOF >&2
usage: $0 [-d DOMAIN] [-p PORT] [-c CAFILE] [-r RETRIES] [-D] [-O] [-P] [-N] [-B]"

Test TLS connection to sha256py docker container to ensure the web service is running.
Tries tests in this order: openssl, python2, ncat, bash.

Any pass will result in zero exit status, any failure will result in nonzero.

optional arguments:
  -d DOMAIN   domain to connect to (default: localhost)
  -p PORT     port to connect to (default: 5000)
  -c CAFILE   certificate file (default: localhost.crt)
  -r RETRIES  number of times to retry a connection (default: 5)
  -D          debug
  -O          force test a connection to service using openssl (best, default)
  -P          force test a connection to service using python2
  -N          force test a connection to service using ncat
  -B          force test a connection to service using bash
  -h          show this help text
EOF
    exit 1
}

debug() {
    if [[ "${DEBUG}" = 'true' ]]; then
        echo "$@" 2>&1
    fi
}

check_pyscript_supported() {
    "${PYTHON2}" "${CHECK_PYSCRIPT}" 'SUPPORTED?'
    return $?
}

if ! check_pyscript_supported ; then
    debug "python check not supported"
fi

while getopts ":d:p:c:r:DOPNB" o; do
    case "${o}" in
        d)
            domain=${OPTARG}
            ;;
        p)
            port=${OPTARG}
            ;;
        c)
            cafile=${OPTARG}
            ;;
        r)
            max_retries=${OPTARG}
            ;;
        D)
            DEBUG='true'
            ;;
        O)
            FORCE_OPENSSL='true'
            ;;
        P)
            FORCE_PYTHON='true'
            ;;
        N)
            FORCE_NETCAT='true'
            ;;
        B)
            FORCE_BASH='true'
            ;;
        h|*)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [[ "${FORCE_OPENSSL}" = true || \
      "${FORCE_PYTHON}" = true || \
      "${FORCE_NETCAT}" = true || \
      "${FORCE_BASH}" = true ]]; then
    FORCE='true'
fi

if [[ -z "${domain}" ]]; then
    domain='localhost'
fi
if [[ -z "${port}" ]]; then
    port='5000'
fi
if [[ -z "${cafile}" ]]; then
    cafile="${SCRIPT_DIR}/../localhost.crt"
fi
if [[ ! -r "${cafile}" ]]; then
    echo 2>&1 "cafile not found"
    exit 1
fi
if [[ -z "${max_retries}" ]]; then
    max_retries='5'
fi

test_openssl_connect() {
    showname
    local attempts=0;
    while true; do
        echo "GET /" | \
            timeout 2 "${OPENSSL}" s_client \
                -CAfile "${cafile}" \
                -connect "${domain}:${port}" &> /dev/null && \
            break
        attempts=$((attempts+1))
        sleep 1
        if [[ "${attempts}" -ge "${max_retries}" ]]; then
            debug 'fail'
            return 1
        fi
    done
    debug 'pass'
    return 0
}

test_python_connect() {
    showname
    if [[ "${DEBUG}" = 'true' ]]; then
        "${PYTHON2}" "${CHECK_PYSCRIPT}" -c "${cafile}" -d "${domain}" \
            -p "${port}" -D
    else
        "${PYTHON2}" "${CHECK_PYSCRIPT}" -c "${cafile}" -d "${domain}" \
            -p "${port}"
    fi
    local result=$?
    [[ "${result}" -eq 0 ]] && debug 'pass' || debug 'fail'
    return "${result}"
}

test_ncat_connect() {
    showname
    timeout "${max_retries}" ncat \
        -C --ssl "${domain}" "${port}" \
        << EOF | grep digest &>/dev/null
POST /messages
Content-Length: 24
Content-Type: application/json

{"message":"foobar2000"}
EOF
    local result=$?
    [[ "${result}" -eq 0 ]] && debug 'pass' || debug 'fail'
    return "${result}"
}

test_bash_connect() {
    showname
    local attempts=0;
    while true; do
        # We sleep 1 here because opening the TCP socket doesn't necessarily
        # mean the rest of the server is ready. Connections may still fail.
        # And we can't (easily) check TLS connectivity with pure bash.
        bash -c \
            "echo -n > /dev/tcp/"${domain}"/"${port}"" &> /dev/null \
            && sleep 1;  break
        attempts=$((attempts+1))
        sleep 1
        if [[ "${attempts}" -ge "${max_retries}" ]]; then
            debug 'fail'
            return 1
        fi
    done
    debug 'pass'
    return 0
}

debug "force: ${FORCE}"
STATUS=0
alias status_return='\
    RESULT=$?; \
    [[ -z "${FORCE}" ]] && exit "${RESULT}"; \
    STATUS=$((RESULT+STATUS))'
if [[ "${FORCE_OPENSSL}" = 'true' ]] || \
   [[ ! "${FORCE}" = 'true' && ! -z "${OPENSSL}" ]]; then
    # Test with OpenSSL. Most reliable.
    test_openssl_connect
    status_return
fi
if [[ "${FORCE_PYTHON}" = 'true' ]] || \
   [[ ! "${FORCE}" = 'true' && ! -z "${PYTHON2}" ]]; then
    # Test with custom Python script. May fail if the user has the wrong
    # version of Python 2 installed (2.6 or earlier).
    test_python_connect
    status_return
fi
if [[ "${FORCE_NETCAT}" = 'true' ]] || \
   [[ ! "${FORCE}" = 'true' && ! -z "${NMAP_NETCAT}" ]]; then
    test_ncat_connect
    status_return
fi
if [[ "${FORCE_BASH}" = 'true' ]] || \
   [[ ! "${FORCE}" = 'true' && "${FORCE_BASH}" = 'true' ]]; then
    test_bash_connect
    status_return
fi
debug "status: ${STATUS}"
exit "${STATUS}"
