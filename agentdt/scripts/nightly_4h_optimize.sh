#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT_DIR/storage/operations/nightly_logs"
RUN_TS="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$LOG_DIR/$RUN_TS"
LOCK_FILE="$LOG_DIR/.nightly_4h.lock"
MAX_SECONDS=$((4 * 60 * 60))
MAX_REPAIR_TARGETS=3
MIN_REPAIR_BUFFER_SECONDS=$((15 * 60))
START_EPOCH="$(date +%s)"
DEADLINE_EPOCH=$((START_EPOCH + MAX_SECONDS))
BACKEND_PID=""
BACKEND_STARTED_BY_SCRIPT=0

mkdir -p "$RUN_DIR"

if [[ -f "$LOCK_FILE" ]]; then
  echo "[nightly] lock exists, previous run may still be active: $LOCK_FILE"
  exit 1
fi

touch "$LOCK_FILE"
cleanup() {
  if [[ "$BACKEND_STARTED_BY_SCRIPT" == "1" && -n "$BACKEND_PID" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
  rm -f "$LOCK_FILE"
}
trap cleanup EXIT

log() {
  echo "[$(date '+%F %T')] $*" | tee -a "$RUN_DIR/nightly.log"
}

time_left() {
  local now
  now="$(date +%s)"
  echo $((DEADLINE_EPOCH - now))
}

run_step() {
  local name="$1"
  shift

  local left
  left="$(time_left)"
  if (( left <= 0 )); then
    log "deadline reached before step: $name"
    return 1
  fi

  log "STEP START: $name (time_left=${left}s)"
  if "$@" >>"$RUN_DIR/nightly.log" 2>&1; then
    log "STEP DONE:  $name"
  else
    log "STEP FAIL:  $name"
    return 1
  fi
}

capture_pytest_summary() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "unknown"
    return 0
  fi
  grep -E '[0-9]+ (passed|failed|error|errors|skipped)' "$file" | tail -n 1 | sed 's/^[[:space:]]*//' || true
}

derive_failure_clusters() {
  : > "$RUN_DIR/failure_clusters.txt"
  : > "$RUN_DIR/failing_test_files.txt"

  if [[ ! -s "$RUN_DIR/failed_tests.txt" ]]; then
    return 0
  fi

  sed -E 's/^FAILED ([^:]+).*/\1/' "$RUN_DIR/failed_tests.txt" |
    sort |
    uniq -c |
    sort -nr > "$RUN_DIR/failure_clusters.txt"

  awk '{print $2}' "$RUN_DIR/failure_clusters.txt" > "$RUN_DIR/failing_test_files.txt"
}

run_priority_suite_verification() {
  local suites=(
    "tests/test_ab_testing.py"
    "tests/test_openclaw_sync.py"
  )
  local suite
  local out_file
  local safe_name

  mkdir -p "$RUN_DIR/priority_suites"
  : > "$RUN_DIR/priority_suites.txt"

  for suite in "${suites[@]}"; do
    [[ -f "$ROOT_DIR/$suite" ]] || continue
    safe_name="${suite//\//_}"
    out_file="$RUN_DIR/priority_suites/${safe_name}.out"
    "$ROOT_DIR/venv/bin/python" -m pytest -q "$suite" > "$out_file" 2>&1 || true
    echo "$suite: $(capture_pytest_summary "$out_file")" >> "$RUN_DIR/priority_suites.txt"
  done
}

run_failing_suite_rechecks() {
  local suite
  local out_file
  local safe_name
  local count=0

  mkdir -p "$RUN_DIR/failing_suite_rechecks"
  : > "$RUN_DIR/failing_suite_rechecks.txt"

  if [[ ! -s "$RUN_DIR/failing_test_files.txt" ]]; then
    echo "No failing suites in baseline" > "$RUN_DIR/failing_suite_rechecks.txt"
    return 0
  fi

  while IFS= read -r suite; do
    [[ -n "$suite" ]] || continue
    count=$((count + 1))
    if (( count > 5 )); then
      break
    fi
    safe_name="${suite//\//_}"
    out_file="$RUN_DIR/failing_suite_rechecks/${safe_name}.out"
    "$ROOT_DIR/venv/bin/python" -m pytest -q "$suite" > "$out_file" 2>&1 || true
    echo "$suite: $(capture_pytest_summary "$out_file")" >> "$RUN_DIR/failing_suite_rechecks.txt"
  done < "$RUN_DIR/failing_test_files.txt"
}

run_bounded_repair_orchestration() {
  local hook_path="$ROOT_DIR/scripts/nightly_repair_slice.sh"
  local hook_available=0
  local suite
  local failure_count
  local safe_name
  local attempt_dir
  local validation_file
  local validation_summary
  local target_count=0
  local left

  mkdir -p "$RUN_DIR/repair_attempts"
  : > "$RUN_DIR/repair_queue.txt"
  : > "$RUN_DIR/repair_orchestration.txt"
  : > "$RUN_DIR/repair_validations.txt"

  if [[ -x "$hook_path" ]]; then
    hook_available=1
  fi

  if [[ ! -s "$RUN_DIR/failure_clusters.txt" ]]; then
    echo "skipped: baseline green" > "$RUN_DIR/repair_orchestration.txt"
    echo "No repair targets queued" > "$RUN_DIR/repair_queue.txt"
    echo "No repair validations were needed" > "$RUN_DIR/repair_validations.txt"
    return 0
  fi

  if (( hook_available == 1 )); then
    echo "mode: hook-enabled ($hook_path)" >> "$RUN_DIR/repair_orchestration.txt"
  else
    echo "mode: queue-only (missing executable hook at $hook_path)" >> "$RUN_DIR/repair_orchestration.txt"
  fi
  echo "max_targets: $MAX_REPAIR_TARGETS" >> "$RUN_DIR/repair_orchestration.txt"
  echo "min_time_buffer_seconds: $MIN_REPAIR_BUFFER_SECONDS" >> "$RUN_DIR/repair_orchestration.txt"

  while read -r failure_count suite; do
    [[ -n "$suite" ]] || continue
    if (( target_count >= MAX_REPAIR_TARGETS )); then
      break
    fi
    target_count=$((target_count + 1))
    echo "$suite | failures=$failure_count | validate=$ROOT_DIR/venv/bin/python -m pytest -q $suite" >> "$RUN_DIR/repair_queue.txt"

    if (( hook_available == 0 )); then
      echo "$suite: queued only (no repo-local repair hook available)" >> "$RUN_DIR/repair_orchestration.txt"
      continue
    fi

    left="$(time_left)"
    if (( left <= MIN_REPAIR_BUFFER_SECONDS )); then
      echo "$suite: skipped repair hook (time_left=${left}s, buffer=${MIN_REPAIR_BUFFER_SECONDS}s)" >> "$RUN_DIR/repair_orchestration.txt"
      continue
    fi

    safe_name="${suite//\//_}"
    attempt_dir="$RUN_DIR/repair_attempts/${target_count}_${safe_name}"
    mkdir -p "$attempt_dir"
    echo "$suite: running repair hook" >> "$RUN_DIR/repair_orchestration.txt"

    if NIGHTLY_REPAIR_TARGET="$suite" NIGHTLY_FAILURE_COUNT="$failure_count" NIGHTLY_RUN_DIR="$RUN_DIR" NIGHTLY_ATTEMPT_DIR="$attempt_dir" "$hook_path" "$suite" > "$attempt_dir/hook.out" 2>&1; then
      echo "$suite: repair hook completed" >> "$RUN_DIR/repair_orchestration.txt"
    else
      echo "$suite: repair hook failed (see $attempt_dir/hook.out)" >> "$RUN_DIR/repair_orchestration.txt"
      continue
    fi

    validation_file="$attempt_dir/validate.out"
    "$ROOT_DIR/venv/bin/python" -m pytest -q "$suite" > "$validation_file" 2>&1 || true
    validation_summary="$(capture_pytest_summary "$validation_file")"
    echo "$suite: ${validation_summary:-unknown}" >> "$RUN_DIR/repair_validations.txt"
  done < "$RUN_DIR/failure_clusters.txt"

  if [[ ! -s "$RUN_DIR/repair_validations.txt" ]]; then
    echo "No repair validations were recorded" > "$RUN_DIR/repair_validations.txt"
  fi
}

run_startup_smoke() {
  local startup_status=""
  local attempt

  : > "$RUN_DIR/startup_check.json"

  if curl -fsS http://127.0.0.1:8080/api/v1/health > /dev/null 2>&1; then
    log "startup smoke using existing backend on :8080"
  elif lsof -ti:8080 > /dev/null 2>&1; then
    cat > "$RUN_DIR/startup_check.json" <<'EOF'
{"status":"skipped","summary":"Skipped startup smoke: port 8080 is busy and health endpoint is unavailable"}
EOF
    return 0
  else
    "$ROOT_DIR/venv/bin/python" "$ROOT_DIR/src/backend/main.py" --port 8080 > "$RUN_DIR/backend_smoke.log" 2>&1 &
    BACKEND_PID="$!"
    BACKEND_STARTED_BY_SCRIPT=1

    for attempt in $(seq 1 30); do
      if curl -fsS http://127.0.0.1:8080/api/v1/health > /dev/null 2>&1; then
        break
      fi
      if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        cat > "$RUN_DIR/startup_check.json" <<'EOF'
{"status":"failed","summary":"Startup smoke failed: backend exited before health endpoint became ready"}
EOF
        return 0
      fi
      sleep 1
    done
  fi

  for attempt in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:8080/api/v1/startup-check > "$RUN_DIR/startup_check.json" 2>/dev/null; then
      startup_status="$(grep -o '"status":"[^"]*"' "$RUN_DIR/startup_check.json" | head -n 1 | cut -d':' -f2 | tr -d '"')"
      if [[ "$startup_status" == "completed" ]]; then
        return 0
      fi
    fi
    sleep 1
  done

  if ! [[ -s "$RUN_DIR/startup_check.json" ]]; then
    cat > "$RUN_DIR/startup_check.json" <<'EOF'
{"status":"skipped","summary":"Startup smoke unavailable: /api/v1/startup-check did not complete in time"}
EOF
  fi
}

emit_markdown_list_or_default() {
  local file="$1"
  local fallback="$2"
  local max_lines="${3:-0}"

  if [[ -s "$file" ]]; then
    if (( max_lines > 0 )); then
      head -n "$max_lines" "$file" | sed 's/^/- /'
    else
      sed 's/^/- /' "$file"
    fi
  else
    echo "- $fallback"
  fi
}

build_summary() {
  local pytest_summary
  local failed_count
  local todo_count
  local startup_summary
  local repair_summary

  pytest_summary="$(capture_pytest_summary "$RUN_DIR/pytest.out")"
  failed_count="$(wc -l < "$RUN_DIR/failed_tests.txt" | tr -d ' ')"
  todo_count="$(wc -l < "$RUN_DIR/todo_markers.txt" | tr -d ' ')"
  startup_summary="$(sed -n 's/.*"summary":"\([^"]*\)".*/\1/p' "$RUN_DIR/startup_check.json" | head -n 1)"
  repair_summary="$(head -n 1 "$RUN_DIR/repair_orchestration.txt" 2>/dev/null || true)"

  cat > "$RUN_DIR/summary.md" <<EOF
# Nightly 4H Summary

## Outcome
- Full pytest baseline: ${pytest_summary:-unknown}
- Failed test signatures captured: ${failed_count}
- TODO/FIXME markers captured: ${todo_count}
- Priority suite verification completed for historical high-ROI clusters.
- Bounded repair orchestration: ${repair_summary:-not recorded}
- Startup smoke summary: ${startup_summary:-not recorded}

## Failure Clusters
$(emit_markdown_list_or_default "$RUN_DIR/failure_clusters.txt" "No failing test clusters in baseline" 5)

## Priority Suite Verification
$(emit_markdown_list_or_default "$RUN_DIR/priority_suites.txt" "No priority suite results recorded")

## Failing Suite Rechecks
$(emit_markdown_list_or_default "$RUN_DIR/failing_suite_rechecks.txt" "No failing suite rechecks were needed")

## Bounded Repair Orchestration
$(emit_markdown_list_or_default "$RUN_DIR/repair_orchestration.txt" "No repair orchestration output recorded")

## Repair Validation
$(emit_markdown_list_or_default "$RUN_DIR/repair_validations.txt" "No repair validations were recorded")

## Artifacts
- git_status.txt
- git_diff_stat.txt
- pytest.out
- failed_tests.txt
- failing_test_files.txt
- failure_clusters.txt
- todo_markers.txt
- priority_suites.txt
- repair_queue.txt
- repair_orchestration.txt
- repair_validations.txt
- startup_check.json
- readme_future_plan.md
- summary.md

## Next Action
EOF

  if (( failed_count > 0 )); then
    cat >> "$RUN_DIR/summary.md" <<EOF
- Review \\\`repair_queue.txt\\\` and \\\`repair_orchestration.txt\\\` before widening beyond the top failing suites.
- If autonomous repair is desired, add a repo-local executable hook at \\\`scripts/nightly_repair_slice.sh\\\` and keep validations bounded to queued suites.
EOF
  else
    cat >> "$RUN_DIR/summary.md" <<EOF
- Baseline is green; spend the next run on automation depth or higher-level product gaps instead of contract repair.
- Keep the repair hook dormant on green runs and only invest in \\\`scripts/nightly_repair_slice.sh\\\` when nightly failures return.
EOF
  fi
}

cd "$ROOT_DIR"

log "nightly 4h run started"
log "run_dir=$RUN_DIR"
log "deadline=$(date -r "$DEADLINE_EPOCH" '+%F %T')"

if [[ -f "$ROOT_DIR/venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/venv/bin/activate"
  log "venv activated"
else
  log "venv not found, aborting"
  exit 1
fi

run_step "capture git status" bash -lc "git status --short > '$RUN_DIR/git_status.txt' && git diff --stat > '$RUN_DIR/git_diff_stat.txt'"
run_step "capture README future plan" bash -lc "awk '/^## 未来计划/{flag=1} flag{print}' README.md > '$RUN_DIR/readme_future_plan.md'"
run_step "run backend tests" bash -lc "'$ROOT_DIR/venv/bin/python' -m pytest -q > '$RUN_DIR/pytest.out' || true"
run_step "extract failed tests" bash -lc "grep -E '^FAILED ' '$RUN_DIR/pytest.out' > '$RUN_DIR/failed_tests.txt' || true"
run_step "derive failure clusters" derive_failure_clusters
run_step "collect TODO markers" bash -lc "rg -n 'TODO|FIXME|NotImplementedError' src/backend src/frontend > '$RUN_DIR/todo_markers.txt' || true"
run_step "run priority suite verification" run_priority_suite_verification
run_step "recheck top failing suites" run_failing_suite_rechecks
run_step "run bounded repair orchestration" run_bounded_repair_orchestration
run_step "run startup smoke" run_startup_smoke
run_step "build nightly summary" build_summary

log "nightly 4h run finished"
