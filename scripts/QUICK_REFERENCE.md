# Safe Push - Quick Reference

## The Only Command You Need

```bash
./scripts/safe-push.sh
```

That's it. The script handles everything.

## What Happens

1. ✓ Checks your working directory is clean
2. ✓ Runs `ruff` linting
3. ✓ Runs `mypy` type checking  
4. ✓ Scans for credentials/secrets/IPs
5. ✓ Shows commits you're about to push
6. ⏸️  Asks for confirmation
7. ✓ Pushes to GitHub
8. ✓ Verifies push succeeded
9. ⏳ Waits for CI to pass
10. ✅ Reports success

## Variants

```bash
# Skip waiting for CI (for quick pushes)
./scripts/safe-push.sh --skip-ci-wait

# Specify branch (default is main)
./scripts/safe-push.sh develop

# Both
./scripts/safe-push.sh --skip-ci-wait develop
```

## When Something Fails

| Error | Cause | Solution |
|-------|-------|----------|
| `Ruff linting failed` | Code style/import issues | Run `ruff check --fix anomyze/` |
| `Mypy type checking failed` | Type annotation errors | Add type hints or cast return values |
| `Potential credentials detected` | Script found suspicious patterns | Review diff, remove if real, or override |
| `Git push failed` | Network or permission issue | Check GitHub access, try again |
| `CI failed` | Tests didn't pass | Check GitHub Actions, fix code, repush |

## What It Scans For (Security)

Automatically blocks pushes containing:
- AWS keys & tokens
- Private keys (RSA, OpenSSH)
- Database credentials
- `.env` files
- OAuth secrets

Warns about (but allows override):
- API tokens
- Hardcoded passwords
- Potential IP addresses

## Setup as Git Alias (Optional)

Add to `~/.gitconfig`:
```ini
[alias]
    safepush = !bash ./scripts/safe-push.sh
```

Then use: `git safepush`

## Files

- `scripts/safe-push.sh` - The script
- `scripts/SAFE_PUSH_GUIDE.md` - Full documentation
- `scripts/QUICK_REFERENCE.md` - This file

## Questions?

See `SAFE_PUSH_GUIDE.md` for complete details.
