# Example Usage Scenarios

This document provides practical examples of how to use the uncommitted changes detection tools.

## Scenario 1: CI/CD Pipeline Check

Before deploying to production, ensure the working directory is clean:

```bash
#!/bin/bash
# deploy.sh

echo "Checking for uncommitted changes..."
if ./check-uncommitted-changes.sh; then
    echo "Proceeding with deployment..."
    # Your deployment commands here
    docker-compose up -d --build
else
    echo "Deployment aborted: Please commit your changes first"
    exit 1
fi
```

## Scenario 2: Pre-build Verification

Before building the application, verify no uncommitted changes:

```bash
# In package.json or Makefile
./check-uncommitted-changes.sh && npm run build
```

## Scenario 3: Automated Testing

Ensure tests run against a clean state:

```bash
#!/bin/bash
# run-tests.sh

if ! ./check-uncommitted-changes.sh; then
    echo "Warning: Running tests with uncommitted changes"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run tests
pytest backend/
npm test --prefix frontend/
```

## Scenario 4: Git Hook Installation

Set up the hooks for a new developer:

```bash
#!/bin/bash
# setup-dev-environment.sh

echo "Setting up Git hooks..."
git config core.hooksPath .githooks

echo "Installing dependencies..."
pip install -r backend/requirements.txt
npm install --prefix frontend/

echo "Environment setup complete!"
```

## Scenario 5: Manual Verification

Quickly check if you have uncommitted work:

```bash
$ ./check-uncommitted-changes.sh
Checking for uncommitted changes...
✓ Working directory is clean
```

Or with uncommitted changes:

```bash
$ ./check-uncommitted-changes.sh
Checking for uncommitted changes...
✗ Uncommitted changes detected!

Modified files:
 M backend/app/main.py
?? temp.txt

Please commit or stash your changes before proceeding.
```

## Scenario 6: Bypass Hooks When Needed

Sometimes you need to commit work-in-progress:

```bash
# Bypass the pre-commit hook
git commit --no-verify -m "WIP: Experimental feature"
```

## Integration with Docker

Add the check to your docker-compose workflow:

```yaml
# In docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    # Pre-build check can be added in Dockerfile
  frontend:
    build: ./frontend
```

Then in your Dockerfile:

```dockerfile
# Dockerfile
FROM python:3.11

# Copy check script
COPY check-uncommitted-changes.sh /app/
RUN chmod +x /app/check-uncommitted-changes.sh

# Run check before building (optional)
# RUN /app/check-uncommitted-changes.sh || echo "Warning: Building with uncommitted changes"

# Rest of your Dockerfile...
```
