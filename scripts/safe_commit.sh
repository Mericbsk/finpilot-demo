#!/usr/bin/env bash
# safe_commit.sh — auto-retry commit when pre-commit auto-fixes files.
#
# Solves the loop:
#   1. ruff-format/ruff modify staged files → commit aborts
#   2. Without re-staging, the fixes sit unstaged → next commit ignores them
#
# Usage:
#   bash scripts/safe_commit.sh "feat: message"
#   make commit MSG="feat: message"
#
# Behavior:
#   - Up to 2 retries: if pre-commit modifies files, re-stage tracked changes and retry.
#   - Stops immediately on real failures (detect-secrets, bandit, syntax errors) and
#     prints a clear message with the offending file/line so user can fix or pragma it.

set -u

MSG="${1:-}"
if [[ -z "$MSG" ]]; then
    echo "ERROR: commit message required" >&2
    echo "Usage: bash scripts/safe_commit.sh \"feat: message\"" >&2
    exit 2
fi

MAX_RETRIES=2
attempt=0

while (( attempt <= MAX_RETRIES )); do
    attempt=$(( attempt + 1 ))
    echo ">> commit attempt $attempt/$((MAX_RETRIES + 1))"

    # Capture both staged file list (before commit) so we know what to re-stage
    staged_before=$(git diff --cached --name-only)
    if [[ -z "$staged_before" ]]; then
        echo "ERROR: nothing staged. Run 'git add <files>' first." >&2
        exit 2
    fi

    output=$(git commit -m "$MSG" 2>&1)
    rc=$?
    echo "$output"

    if (( rc == 0 )); then
        echo "✓ commit OK"
        exit 0
    fi

    # Real failures — stop and let user fix
    if echo "$output" | grep -qE "Secret Type:|Possible hardcoded password|bandit.*Failed|SyntaxError"; then
        echo "" >&2
        echo "❌ Real failure (not auto-fixable). Fix the issue above and retry." >&2
        echo "   For false-positive secrets, add '# pragma: allowlist secret' on the line." >&2
        exit 1
    fi

    # Auto-fix loop: pre-commit modified files → re-stage and retry
    if echo "$output" | grep -qE "files were modified by this hook|files reformatted|errors.*fixed"; then
        echo ">> pre-commit auto-fixed files, re-staging and retrying..."
        # Re-stage only the files that were originally staged
        echo "$staged_before" | xargs -r git add --
        continue
    fi

    # Unknown failure
    echo "" >&2
    echo "❌ Commit failed (unknown reason). See output above." >&2
    exit 1
done

echo "❌ Gave up after $MAX_RETRIES retries — investigate manually." >&2
exit 1
