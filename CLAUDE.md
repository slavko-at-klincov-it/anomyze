# Anomyze

## Pushing to GitHub

Use `./scripts/safe-push.sh` to push safely. It validates code (ruff, mypy), scans for credentials/secrets, verifies the push, and waits for CI to pass. See `scripts/SAFE_PUSH_GUIDE.md` for details.

## Testing

- NEVER run multiple pytest processes in parallel. Always wait for one test run to complete before starting another.
- Tests load ~8 GB of ML models per process. Only one test run at a time.
