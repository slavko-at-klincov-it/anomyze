# Safe Push to GitHub - Complete Guide

## Overview

`safe-push.sh` is a comprehensive pre-push validation and security review script that ensures all code changes meet quality and security standards before being pushed to GitHub. It automates the checks that were manually done during the CI troubleshooting.

## What It Does

### 1. **Pre-Push Validation**
   - ✓ Verifies working directory is clean (no uncommitted changes)
   - ✓ Confirms you're on the correct branch (default: `main`)
   - ✓ Runs `ruff` linting checks
   - ✓ Runs `mypy` type checking

### 2. **Security Review**
Automatically scans for sensitive data:
   - AWS credentials and access keys
   - Private keys (RSA, OpenSSH, etc.)
   - API tokens and Bearer tokens
   - Hardcoded passwords
   - Database connection strings with credentials
   - IP addresses (with filters for common non-sensitive ones)
   - OAuth and API secrets
   - Environment variable secrets in code
   - Committed `.env` files

### 3. **Push & Verification**
   - Shows commits to be pushed for manual review
   - Pushes to GitHub
   - Verifies the push succeeded
   - Monitors CI pipeline until completion (or allows skipping)
   - Confirms CI passes before reporting success

## Usage

### Basic Usage
```bash
./scripts/safe-push.sh
```

This will:
1. Run all validations on the `main` branch
2. Wait for CI to complete and pass

### Skip CI Wait
```bash
./scripts/safe-push.sh --skip-ci-wait
```

Push to GitHub but don't wait for CI to finish. Useful for quick pushes when you're confident.

### Push Different Branch
```bash
./scripts/safe-push.sh main    # explicit branch name
./scripts/safe-push.sh --skip-ci-wait develop  # skip wait on different branch
```

## Step-by-Step Process

1. **Git Status Check**
   - Ensures no uncommitted changes
   - Prevents accidental loss of work

2. **Branch Verification**
   - Confirms you're on the target branch
   - Prevents pushing to wrong branch

3. **Ruff Linting** (handles import sorting, code style)
   - Runs: `ruff check anomyze/`
   - Catches: unsorted imports, style violations, complexity issues

4. **Mypy Type Checking** (handles type safety)
   - Runs: `mypy anomyze/ --ignore-missing-imports`
   - Catches: type annotation errors, return type mismatches

5. **Security Review** (the comprehensive scan)
   - Scans all changed files for 8 categories of sensitive data
   - Allows override with confirmation prompt if issues found
   - **Never blocks on low-confidence warnings**, only on high-confidence issues

6. **Commit Review**
   - Shows all commits that will be pushed
   - Requires explicit confirmation before proceeding

7. **GitHub Push**
   - Executes `git push origin <branch>`

8. **Push Verification**
   - Confirms local and remote are synchronized
   - Verifies GitHub received the push

9. **CI Monitoring** (optional)
   - Polls GitHub Actions for CI status
   - Waits up to 30 minutes for completion
   - Reports success/failure
   - Can be skipped with `--skip-ci-wait` flag

## Security Scanning Details

### High-Confidence Detections (Block Push)
- Private keys (PEM format)
- Database credentials (PostgreSQL, MySQL, MongoDB)
- `.env` files
- OAuth/API secrets

### Medium-Confidence Detections (Warn & Allow Override)
- AWS credentials
- API tokens
- Hardcoded passwords
- IP addresses (filtered for common non-sensitive patterns)

### What It Doesn't Check
- Source code logic for security vulnerabilities (use dedicated security scanners for that)
- Secrets in commit history (use `git-secrets` or `gitleaks` for that)
- Configuration in `.gitignore`'d files (those won't be scanned)

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - pushed and (if applicable) CI passed |
| 1 | Validation failed or user cancelled |

## Common Scenarios

### Scenario: Linting Fails
```
[✗] Ruff linting failed
anomyze/pipeline/recognizers/austrian.py:8: I001 Import block is unsorted
```

**Fix:**
```bash
# Fix the specific issue (e.g., ruff auto-fix)
ruff check --fix anomyze/

# Re-run safe-push
./scripts/safe-push.sh
```

### Scenario: Type Check Fails
```
[✗] Mypy type checking failed
anomyze/api/endpoints.py:42: error: Returning Any from function declared to return "str"
```

**Fix:**
```bash
# Add explicit type casting or annotations
# Then re-run
./scripts/safe-push.sh
```

### Scenario: Security Warning Appears
```
[WARN] Potential API tokens detected in diff
Continue anyway? (y/n)
```

**Decision Point:**
- If you added credentials intentionally: **DO NOT CONTINUE** - remove them
- If it's a false positive (e.g., documenting API format): Type `y` to override

### Scenario: CI Fails After Push
The script will exit with status 1 and show:
```
[✗] CI failed!
  Title:  Test on Python 3.11
  Status: failure
  Run ID: 24772232261
```

Visit the GitHub Actions link to debug and fix.

## Environment Requirements

- Git (with `gh` CLI configured)
- Python with `ruff` and `mypy` installed
- Bash shell
- GitHub CLI (`gh`) installed and authenticated

## Integration with Your Workflow

### Option 1: Manual Usage
Run before every `git push`:
```bash
./scripts/safe-push.sh
```

### Option 2: Git Alias
Add to your `~/.gitconfig`:
```ini
[alias]
    safepush = !bash ./scripts/safe-push.sh
```

Then use: `git safepush`

### Option 3: Automated (Git Hook)
Create `.git/hooks/pre-push`:
```bash
#!/bin/bash
./scripts/safe-push.sh
```

Make executable: `chmod +x .git/hooks/pre-push`

## Troubleshooting

### "ruff not found"
```bash
pip install ruff
# or
pip install -e ".[dev]"
```

### "mypy not found"
```bash
pip install mypy
```

### "gh not found"
Install GitHub CLI: https://cli.github.com/

### Script hangs on CI monitoring
- The script polls every 10 seconds for up to 30 minutes
- If CI takes longer, either:
  - Wait and it will auto-complete
  - Press `Ctrl+C` to cancel and check GitHub manually

### Security scanner is too aggressive
Edit the regex patterns in the script's Step 5 to fine-tune detection. Common patterns to adjust:
- IP address regex (currently filters common private IPs)
- Password pattern (adjust minimum length)
- Token patterns

## Learning from CI Failures

This script encodes lessons from the `anomyze` project's CI troubleshooting:

1. **Import Sorting** - ruff I001 rule prevents unsorted imports (stdlib → third-party → local)
2. **Type Safety** - mypy ensures return types match declarations
3. **Security** - Prevents accidental credential commits
4. **Verification** - Confirms push actually reached GitHub
5. **CI Validation** - Waits for tests to pass before declaring success

## Future Enhancements

Possible improvements:
- [ ] Add pytest execution before push
- [ ] Add commit message validation (conventional commits)
- [ ] Add branch protection checks
- [ ] Integration with pre-commit framework
- [ ] Support for multiple security scanning tools
- [ ] Detailed security report generation
- [ ] Integration with SAST tools

## Questions?

If the script behavior seems unexpected:
1. Check your changes: `git log origin/main..HEAD -p`
2. Verify linting locally: `ruff check anomyze/`
3. Check types locally: `mypy anomyze/`
4. Review security scan manually: `git diff origin/main HEAD`
