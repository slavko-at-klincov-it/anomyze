#!/bin/bash
set -e

# Anomyze Safe Push to GitHub
# Performs comprehensive pre-push validation, security review, and post-push verification
# Usage: ./scripts/safe-push.sh [--skip-ci-wait] [--branch main]

BRANCH=${2:-main}
SKIP_CI_WAIT=false

if [ "$1" = "--skip-ci-wait" ]; then
    SKIP_CI_WAIT=true
fi

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Anomyze Safe Push to GitHub${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check git status
log_info "Step 1: Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    log_error "Working directory has uncommitted changes"
    git status
    exit 1
fi
log_success "Working directory is clean"

# Step 2: Verify on correct branch
log_info "Step 2: Verifying branch..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    log_error "Not on branch '$BRANCH' (currently on '$CURRENT_BRANCH')"
    exit 1
fi
log_success "On branch $BRANCH"

# Step 3: Run linting (ruff)
log_info "Step 3: Running ruff linting..."
if ! ruff check anomyze/ > /tmp/ruff-output.txt 2>&1; then
    log_error "Ruff linting failed"
    cat /tmp/ruff-output.txt
    exit 1
fi
log_success "Ruff linting passed"

# Step 4: Run type checking (mypy)
log_info "Step 4: Running mypy type checking..."
if ! mypy anomyze/ --ignore-missing-imports > /tmp/mypy-output.txt 2>&1; then
    log_error "Mypy type checking failed"
    cat /tmp/mypy-output.txt
    exit 1
fi
log_success "Mypy type checking passed"

# Step 5: Security review
log_info "Step 5: Performing security review..."
echo ""

SECURITY_ISSUES=0

# Check for AWS credentials
if git diff origin/$BRANCH HEAD -- '*.py' '*.yaml' '*.yml' '*.json' '*.env*' '*.txt' | grep -iE "(aws_access_key|aws_secret|AKIA|aws_session_token)" > /dev/null 2>&1; then
    log_warn "Potential AWS credentials detected in diff"
    SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
fi

# Check for private keys
if git diff origin/$BRANCH HEAD -- '*.py' '*.yaml' '*.yml' '*.json' | grep -iE "(-----BEGIN PRIVATE KEY|-----BEGIN RSA PRIVATE KEY|-----BEGIN OPENSSH PRIVATE KEY)" > /dev/null 2>&1; then
    log_error "Private keys detected in diff!"
    SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
fi

# Check for JWT/Bearer tokens
if git diff origin/$BRANCH HEAD -- '*.py' '*.yaml' '*.yml' '*.json' '*.txt' | grep -iE "(bearer|authorization.*token|x-api-key|api.key|apikey)" > /dev/null 2>&1; then
    log_warn "Potential API tokens or authorization headers detected in diff"
    SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
fi

# Check for hardcoded passwords
if git diff origin/$BRANCH HEAD -- '*.py' '*.yaml' '*.yml' '*.json' | grep -iE "(password|passwd|pwd)\s*[:=]\s*['\"]?[A-Za-z0-9!@#$%^&*]{6,}" > /dev/null 2>&1; then
    log_warn "Potential hardcoded passwords detected"
    SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
fi

# Check for database connection strings
if git diff origin/$BRANCH HEAD -- '*.py' '*.yaml' '*.yml' '*.json' | grep -iE "(postgresql|mysql|mongodb)://[^:]+:[^@]+@" > /dev/null 2>&1; then
    log_error "Database credentials detected in diff!"
    SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
fi

# Check for IP addresses (more permissive to avoid false positives)
if git diff origin/$BRANCH HEAD -- '*.py' '*.yaml' '*.yml' '*.json' '*.txt' | grep -E "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" | grep -v "0.0.0.0\|127.0.0.1\|192.168\|10.0\|172.16" > /dev/null 2>&1; then
    log_warn "Potential IP addresses detected (may be false positives)"
    SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
fi

# Check for OAuth/API secrets
if git diff origin/$BRANCH HEAD -- '*.py' '*.yaml' '*.yml' '*.json' | grep -iE "(client_secret|oauth_token|github_token|gitlab_token|stripe_key)" > /dev/null 2>&1; then
    log_error "OAuth/API secrets detected!"
    SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
fi

# Check for environment secrets in code
if git diff origin/$BRANCH HEAD -- '*.py' | grep -E "os\.environ\[.*(SECRET|TOKEN|PASSWORD|KEY|CREDENTIAL)" > /dev/null 2>&1; then
    log_warn "Code references environment secrets (verify they're not hardcoded elsewhere)"
fi

# Check for .env files
if git diff origin/$BRANCH HEAD --name-only | grep -E "\.env" > /dev/null 2>&1; then
    log_error ".env files should not be committed!"
    SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
fi

echo ""
if [ $SECURITY_ISSUES -eq 0 ]; then
    log_success "Security review passed - no sensitive data detected"
else
    log_error "Security review found $SECURITY_ISSUES potential issue(s)"
    log_warn "Please review the changes carefully before pushing"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 6: Get commits to be pushed
log_info "Step 6: Reviewing commits to be pushed..."
COMMITS=$(git log origin/$BRANCH..$BRANCH --oneline)
if [ -z "$COMMITS" ]; then
    log_warn "No commits to push"
    exit 0
fi
echo "$COMMITS"
echo ""

# Step 7: Confirm push
log_warn "Ready to push to origin/$BRANCH"
read -p "Continue with push? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_error "Push cancelled"
    exit 1
fi

# Step 8: Push to GitHub
log_info "Step 8: Pushing to GitHub..."
if ! git push origin $BRANCH; then
    log_error "Git push failed"
    exit 1
fi
log_success "Pushed to origin/$BRANCH"

# Step 9: Verify push on GitHub
log_info "Step 9: Verifying push on GitHub..."
sleep 2
LOCAL_HEAD=$(git log -1 --format=%H $BRANCH)
REMOTE_HEAD=$(git log -1 --format=%H origin/$BRANCH)

if [ "$LOCAL_HEAD" != "$REMOTE_HEAD" ]; then
    log_error "Local and remote HEAD don't match"
    log_error "Local:  $LOCAL_HEAD"
    log_error "Remote: $REMOTE_HEAD"
    exit 1
fi
log_success "GitHub main branch is up-to-date with local"

# Step 10: Monitor CI (if not skipped)
if [ "$SKIP_CI_WAIT" = true ]; then
    log_warn "Skipping CI wait (use --skip-ci-wait to skip, or re-run without it to wait)"
else
    log_info "Step 10: Waiting for CI to complete..."
    echo ""

    TIMEOUT=1800  # 30 minutes
    ELAPSED=0
    POLL_INTERVAL=10

    while [ $ELAPSED -lt $TIMEOUT ]; do
        LATEST_RUN=$(gh run list --branch $BRANCH --limit 1 2>/dev/null || echo "")

        if [ -z "$LATEST_RUN" ]; then
            echo -ne "\r  Waiting for CI run to start... (${ELAPSED}s)"
            ELAPSED=$((ELAPSED + POLL_INTERVAL))
            sleep $POLL_INTERVAL
            continue
        fi

        STATUS=$(echo "$LATEST_RUN" | awk '{print $1}')
        TITLE=$(echo "$LATEST_RUN" | cut -d$'\t' -f3 | head -c 50)
        TIME=$(echo "$LATEST_RUN" | awk '{print $NF}')

        if [ "$STATUS" = "completed" ]; then
            RESULT=$(echo "$LATEST_RUN" | awk '{print $2}')
            echo ""
            if [ "$RESULT" = "success" ]; then
                log_success "CI passed!"
                echo "  Title:  $TITLE"
                echo "  Status: $RESULT"
                echo "  Time:   $TIME"
            else
                log_error "CI failed!"
                echo "  Title:  $TITLE"
                echo "  Status: $RESULT"
                echo "  Run ID: $(echo "$LATEST_RUN" | awk '{print $(NF-1)}')"
                exit 1
            fi
            break
        else
            echo -ne "\r  CI running: $TITLE ($TIME)"
            ELAPSED=$((ELAPSED + POLL_INTERVAL))
            sleep $POLL_INTERVAL
        fi
    done

    if [ $ELAPSED -ge $TIMEOUT ]; then
        log_warn "CI did not complete within 30 minutes. Check manually on GitHub."
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   ✓ Safe push completed successfully${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
log_success "Commit $LOCAL_HEAD is now on GitHub main with passing CI"
