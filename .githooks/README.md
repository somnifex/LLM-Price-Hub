# Git Hooks for LLM Price Hub

This directory contains Git hooks to help maintain code quality and prevent common issues.

## Available Hooks

### pre-commit

The pre-commit hook runs automatically before each commit and performs the following checks:

1. **Changes Detection**: Verifies that there are changes to commit
2. **Untracked Files Warning**: Alerts you if there are untracked files that might need to be added

## Installation

To enable these hooks, run the following command from the repository root:

```bash
git config core.hooksPath .githooks
```

This tells Git to use hooks from the `.githooks` directory instead of the default `.git/hooks` directory.

## Disabling Hooks Temporarily

If you need to bypass the hooks for a specific commit, use the `--no-verify` flag:

```bash
git commit --no-verify -m "Your commit message"
```

## Hook Behavior

- The pre-commit hook will warn you about untracked files and ask for confirmation before proceeding
- You can choose to continue or abort the commit
- The hook uses colored output to make warnings more visible

## Manual Check

You can also manually check for uncommitted changes using the utility script:

```bash
./check-uncommitted-changes.sh
```

This script will:
- Check for modified files (staged or unstaged)
- Check for untracked files
- Exit with code 0 if clean, 1 if issues detected

This is useful for CI/CD pipelines or before running deployments.
