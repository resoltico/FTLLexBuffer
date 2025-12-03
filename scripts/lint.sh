#!/usr/bin/env bash
# ==============================================================================
# lint.sh — Deterministic Hybrid (AI/Human) Linter
# ==============================================================================
# COMPATIBILITY: Bash v5.0+
# ==============================================================================

if ((BASH_VERSINFO[0] < 5)); then
    echo "::error::[FATAL] Bash v5.0+ required. Found: ${BASH_VERSION}"
    exit 1
fi

# Strict Modes (Guaranteed ON)
set -o errexit
set -o nounset
set -o pipefail

# --- 1. SETUP & UTILS ---
CLEAN_CACHE=true
declare -A STATUS
declare -A TIMING
declare -A METRICS
FAILED=false
IS_GHA="${GITHUB_ACTIONS:-false}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-clean) CLEAN_CACHE=false; shift ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

# Colors
if [[ "${NO_COLOR:-}" == "1" ]]; then
    RED=""; GREEN=""; YELLOW=""; BLUE=""; CYAN=""; BOLD=""; RESET=""
else
    RED="\033[31m"; GREEN="\033[32m"; YELLOW="\033[33m"; BLUE="\033[34m"; CYAN="\033[36m"; BOLD="\033[1m"; RESET="\033[0m"
fi

log_group_start() { [[ "$IS_GHA" == "true" ]] && echo "::group::$1"; echo -e "\n${BOLD}${CYAN}=== $1 ===${RESET}"; }
log_group_end() { [[ "$IS_GHA" == "true" ]] && echo "::endgroup::"; return 0; }
log_info() { echo -e "${BLUE}[INFO]${RESET} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${RESET} $1"; }
log_fail() { echo -e "${RED}[FAIL]${RESET} $1"; }
log_pass() { echo -e "${GREEN}[PASS]${RESET} $1"; }
log_err()  { echo -e "${RED}[ERROR]${RESET} $1" >&2; }

# Safe Tool Resolver (No subshells, uses Nameref, handles errors internally)
resolve_tool() {
    local cmd="$1"
    local -n out_ref="$2"
    
    if [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/$cmd" ]]; then
        out_ref="$VIRTUAL_ENV/bin/$cmd"
        log_info "$cmd resolved to: $out_ref (VENV)"
        return 0
    fi
    
    local path_result=""
    set +e 
    path_result="$(command -v "$cmd" 2>/dev/null)"
    local exit_code=$?
    set -e
    
    if [[ $exit_code -eq 0 ]]; then
        out_ref="$path_result"
        log_info "$cmd resolved to: $out_ref (PATH)"
        return 0
    fi

    if [[ -x ".venv/bin/$cmd" ]]; then
        out_ref=".venv/bin/$cmd"
        log_info "$cmd resolved to: $out_ref (Local VENV)"
        return 0
    fi

    out_ref="$cmd"
    return 1
}

# --- 2. EXECUTION ---
# --- ASSUMPTIONS TESTER ---
pre_flight_diagnostics() {
    log_group_start "Pre-Flight Diagnostics"
    log_info "Bash Version: ${BASH_VERSION}"
    log_info "Shell Strictness: errexit, nounset, pipefail are all globally ON."
    
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        log_info "VIRTUAL_ENV: Active at ${VIRTUAL_ENV}"
    else
        log_warn "VIRTUAL_ENV: Not active."
    fi

    local status=0
    if ! resolve_tool "ruff" RUFF_BIN; then status=1; log_err "Ruff MISSING." ; else log_pass "Ruff Found: $RUFF_BIN" ; fi
    if ! resolve_tool "mypy" MYPY_BIN; then status=1; log_err "MyPy MISSING." ; else log_pass "MyPy Found: $MYPY_BIN" ; fi
    if ! resolve_tool "pylint" PYLINT_BIN; then status=1; log_err "Pylint MISSING." ; else log_pass "Pylint Found: $PYLINT_BIN" ; fi
    
    if [[ $status -ne 0 ]]; then log_err "One or more lint tools are missing. Run 'pip install .[dev]'." ; exit 1 ; fi
    log_group_end
}
pre_flight_diagnostics

# Navigation
PROJECT_ROOT="$PWD"
while [[ "$PROJECT_ROOT" != "/" && ! -f "$PROJECT_ROOT/pyproject.toml" ]]; do
    PROJECT_ROOT="$(dirname "$PROJECT_ROOT")"
done
if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
    log_err "pyproject.toml not found."
    exit 1
fi
cd "$PROJECT_ROOT"
PYPROJECT_CONFIG="$PROJECT_ROOT/pyproject.toml"

# Cleaning
if [[ "$CLEAN_CACHE" == "true" ]]; then
    log_group_start "Housekeeping"
    log_info "Cleaning caches..."
    rm -rf .mypy_cache .pylint.d .ruff_cache
    set +e
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    set -e
    log_info "Caches cleared."
    log_group_end
fi

# Define Targets
declare -a TARGETS=()
[[ -d "src" ]] && TARGETS+=("src")
[[ -d "tests" ]] && TARGETS+=("tests")
[[ -d "test" ]] && TARGETS+=("test")
[[ -d "examples" ]] && TARGETS+=("examples")

record_result() {
    local tool="$1" target="$2" status="$3"
    local duration="${4:-0}" files="${5:-0}"
    STATUS["${tool}|${target}"]="$status"
    TIMING["${tool}|${target}"]="$duration"
    METRICS["${tool}|${target}"]="$files"
    [[ "$status" == "fail" ]] && FAILED=true
    return 0
}

# --- 3. RUNNERS (Wrapped with set +e for robustness) ---
run_ruff() {
    log_group_start "Lint: Ruff"
    log_info "Running Ruff on: ${TARGETS[*]}"

    local start_time="${EPOCHREALTIME}"
    local file_count=0

    set +e
    for target in "${TARGETS[@]}"; do
        local count=$(find "$target" -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
        file_count=$((file_count + count))
    done
    set -e

    set +e # CRITICAL: Temporarily disable errexit
    "$RUFF_BIN" check --config "$PYPROJECT_CONFIG" "${TARGETS[@]}"
    local ruff_exit_code=$?
    set -e # Restore errexit

    local end_time="${EPOCHREALTIME}"
    local duration=$(printf "%.3f" "$(echo "$end_time - $start_time" | bc)")

    if [[ $ruff_exit_code -eq 0 ]]; then
        log_pass "Ruff passed."
        record_result "ruff" "all" "pass" "$duration" "$file_count"
    else
        log_fail "Ruff found issues (Exit Code: $ruff_exit_code)."
        record_result "ruff" "all" "fail" "$duration" "$file_count"
    fi
    log_group_end
}

run_mypy() {
    log_group_start "Lint: MyPy"
    local mypy_global_status=0

    for dir in "${TARGETS[@]}"; do
        local conf_args=("--config-file" "$PYPROJECT_CONFIG")
        if [[ "$dir" != "src" && -f "$dir/mypy.ini" ]]; then
            conf_args=("--config-file" "$dir/mypy.ini")
        fi
        log_info "Checking $dir..."

        local start_time="${EPOCHREALTIME}"
        local output_file=$(mktemp)

        set +e
        "$MYPY_BIN" "${conf_args[@]}" "$dir" 2>&1 | tee "$output_file"
        local mypy_exit_code=$?
        set -e

        local end_time="${EPOCHREALTIME}"
        local duration=$(printf "%.3f" "$(echo "$end_time - $start_time" | bc)")

        local file_count=0
        set +e
        file_count=$(grep -o 'no issues found in [0-9]* source files' "$output_file" 2>/dev/null | grep -o '[0-9]*' | head -1 || echo "0")
        [[ -z "$file_count" ]] && file_count=0
        set -e
        rm -f "$output_file"

        if [[ $mypy_exit_code -eq 0 ]]; then
             record_result "mypy" "$dir" "pass" "$duration" "$file_count"
        else
             mypy_global_status=1
             record_result "mypy" "$dir" "fail" "$duration" "$file_count"
        fi
    done

    if [[ $mypy_global_status -eq 0 ]]; then
        log_pass "MyPy passed all targets."
    else
        log_fail "MyPy found issues in one or more targets."
    fi
    log_group_end
}

run_pylint() {
    log_group_start "Lint: Pylint"
    local pylint_global_status=0

    for dir in "${TARGETS[@]}"; do
        local conf_args=("--rcfile" "$PYPROJECT_CONFIG")
        if [[ "$dir" != "src" && -f "$dir/.pylintrc" ]]; then
            conf_args=("--rcfile" "$dir/.pylintrc")
        fi
        log_info "Analyzing $dir..."

        local start_time="${EPOCHREALTIME}"
        local file_count=0

        set +e
        file_count=$(find "$dir" -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
        set -e

        set +e
        "$PYLINT_BIN" "${conf_args[@]}" "$dir"
        local pylint_exit_code=$?
        set -e

        local end_time="${EPOCHREALTIME}"
        local duration=$(printf "%.3f" "$(echo "$end_time - $start_time" | bc)")

        if [[ $pylint_exit_code -eq 0 ]]; then
            record_result "pylint" "$dir" "pass" "$duration" "$file_count"
        else
            pylint_global_status=1
            record_result "pylint" "$dir" "fail" "$duration" "$file_count"
        fi
    done

    if [[ $pylint_global_status -eq 0 ]]; then
        log_pass "Pylint passed all targets."
    else
        log_fail "Pylint found issues in one or more targets."
    fi
    log_group_end
}

run_ruff
run_mypy
run_pylint

# --- REPORT ---
log_group_start "Final Report"
echo "[SUMMARY-JSON-BEGIN]"
printf "{"
first=1
for key in "${!STATUS[@]}"; do
    [[ $first -eq 0 ]] && printf ","
    printf "\"%s\":{" "$key"
    printf "\"status\":\"%s\"," "${STATUS[$key]}"
    printf "\"duration_sec\":\"%s\"," "${TIMING[$key]}"
    printf "\"files\":\"%s\"" "${METRICS[$key]}"
    printf "}"
    first=0
done
printf "}\n"
echo "[SUMMARY-JSON-END]"

if [[ "$FAILED" == "true" ]]; then
    exit 1
else
    exit 0
fi