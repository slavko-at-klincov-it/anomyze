# Anomyze

## Testing

- NEVER run multiple pytest processes in parallel. Always wait for one test run to complete before starting another.
- Tests load ~8 GB of ML models per process. Only one test run at a time.
