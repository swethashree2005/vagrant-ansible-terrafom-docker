#!/usr/bin/env bash
set -euo pipefail

# Required: GITHUB_REPO in the form owner/repo
: "${GITHUB_REPO:?GITHUB_REPO environment variable must be set (e.g., owner/repo)}"

RUNNER_DIR=/opt/actions-runner
cd "$RUNNER_DIR"

# Optional: RUNNER_NAME, RUNNER_LABELS, RUNNER_WORKDIR, GITHUB_PAT, RUNNER_TOKEN
RUNNER_NAME=${RUNNER_NAME:-$(hostname)-runner}
RUNNER_LABELS=${RUNNER_LABELS:-self-hosted,lab}
RUNNER_WORKDIR=${RUNNER_WORKDIR:-_work}

get_registration_token() {
  if [[ -n "${RUNNER_TOKEN:-}" ]]; then
    echo "$RUNNER_TOKEN"
    return 0
  fi
  if [[ -z "${GITHUB_PAT:-}" ]]; then
    echo "Either RUNNER_TOKEN or GITHUB_PAT must be provided via env" >&2
    exit 1
  fi
  echo "Requesting registration token for $GITHUB_REPO ..."
  curl -fsSL -X POST \
    -H "Authorization: token ${GITHUB_PAT}" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/${GITHUB_REPO}/actions/runners/registration-token" \
    | jq -r .token
}

remove_runner() {
  echo "Stopping runner..."
  ./svc.sh stop || true
  echo "Removing runner config..."
  ./config.sh remove --unattended || true
}

trap 'remove_runner' TERM INT EXIT

TOKEN=$(get_registration_token)

# Ensure dependencies are installed (no-op if already)
./bin/installdependencies.sh || true

# Configure runner (idempotent-ish if rerun after removal)
./config.sh \
  --url "https://github.com/${GITHUB_REPO}" \
  --token "${TOKEN}" \
  --name "${RUNNER_NAME}" \
  --work "${RUNNER_WORKDIR}" \
  --labels "${RUNNER_LABELS}" \
  --unattended

# Start the service in foreground
exec ./run.sh
