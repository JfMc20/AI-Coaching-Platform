# Git Workflow and Version Control Guidelines

## Overview

This document establishes the Git workflow, branching strategy, commit conventions, pull request process, and release management procedures for the multi-channel proactive coaching platform development team.

## Branching Strategy

### GitFlow Model
We use a modified GitFlow model optimized for continuous deployment and feature development:

```
main (production)
├── develop (integration)
│   ├── feature/user-authentication
│   ├── feature/ai-conversation-engine
│   ├── feature/mobile-app-ui
│   └── hotfix/critical-security-patch
├── release/v1.2.0
└── hotfix/urgent-bug-fix
```

### Branch Types and Naming

#### Main Branches
```bash
# Production branch - always deployable
main

# Development integration branch
develop
```

#### Supporting Branches
```bash
# Feature branches - new functionality
feature/short-description
feature/user-profile-management
feature/whatsapp-integration
feature/ai-response-optimization

# Release branches - preparing for production
release/v1.2.0
release/v2.0.0-beta

# Hotfix branches - critical production fixes
hotfix/security-vulnerability-fix
hotfix/payment-processing-bug

# Bugfix branches - non-critical fixes
bugfix/conversation-memory-leak
bugfix/mobile-app-crash
```

### Branch Lifecycle

#### Feature Branch Workflow
```bash
# 1. Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/ai-conversation-engine

# 2. Work on feature with regular commits
git add .
git commit -m "feat: implement basic conversation flow"
git commit -m "feat: add context memory management"
git commit -m "test: add conversation engine unit tests"

# 3. Keep feature branch updated
git checkout develop
git pull origin develop
git checkout feature/ai-conversation-engine
git rebase develop

# 4. Push feature branch
git push origin feature/ai-conversation-engine

# 5. Create pull request to develop
# (via GitHub/GitLab interface)

# 6. After merge, clean up
git checkout develop
git pull origin develop
git branch -d feature/ai-conversation-engine
git push origin --delete feature/ai-conversation-engine
```

#### Release Branch Workflow
```bash
# 1. Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0

# 2. Finalize release (version bumps, documentation)
git commit -m "chore: bump version to 1.2.0"
git commit -m "docs: update changelog for v1.2.0"

# 3. Merge to main and develop
git checkout main
git merge --no-ff release/v1.2.0
git tag -a v1.2.0 -m "Release version 1.2.0"

git checkout develop
git merge --no-ff release/v1.2.0

# 4. Push changes and clean up
git push origin main
git push origin develop
git push origin v1.2.0
git branch -d release/v1.2.0
git push origin --delete release/v1.2.0
```

## Commit Message Conventions

### Conventional Commits Format
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types
```bash
# Features - new functionality
feat: add user authentication system
feat(api): implement conversation endpoints
feat(mobile): add push notification support

# Bug fixes
fix: resolve memory leak in conversation manager
fix(ui): correct button alignment on mobile
fix(api): handle null user profile gracefully

# Documentation
docs: update API documentation
docs(readme): add installation instructions
docs: add code examples for AI integration

# Code style/formatting
style: fix linting errors in user service
style: apply prettier formatting to components

# Refactoring
refactor: extract conversation logic into service
refactor(ai): simplify response generation pipeline

# Performance improvements
perf: optimize database queries for user lookup
perf(mobile): reduce app startup time

# Tests
test: add unit tests for user profile service
test(integration): add API endpoint tests
test: increase coverage for AI conversation module

# Build/CI changes
build: update Docker configuration
ci: add automated testing pipeline
build(deps): upgrade FastAPI to v0.104.0

# Chores/maintenance
chore: update dependencies
chore: clean up unused imports
chore(release): prepare v1.2.0 release
```

### Commit Message Examples
```bash
# Good commit messages
git commit -m "feat(auth): implement JWT token refresh mechanism

- Add refresh token endpoint
- Update token validation middleware
- Add tests for token refresh flow

Closes #123"

git commit -m "fix(mobile): resolve crash on conversation load

The app was crashing when loading conversations with large
message histories due to memory pressure. This fix implements
pagination and lazy loading to resolve the issue.

Fixes #456"

git commit -m "docs(api): add examples for conversation endpoints

- Add request/response examples
- Document error codes
- Include authentication requirements"

# Bad commit messages (avoid these)
git commit -m "fix stuff"
git commit -m "WIP"
git commit -m "updates"
git commit -m "fixed the bug"
```

### Commit Best Practices
```bash
# 1. Make atomic commits (one logical change per commit)
# Good:
git commit -m "feat: add user registration endpoint"
git commit -m "test: add tests for user registration"

# Bad:
git commit -m "feat: add user registration and fix login bug and update docs"

# 2. Use imperative mood in subject line
# Good:
git commit -m "fix: resolve authentication timeout issue"

# Bad:
git commit -m "fixed authentication timeout issue"
git commit -m "fixes authentication timeout issue"

# 3. Limit subject line to 50 characters
# Good:
git commit -m "feat: add conversation memory management"

# Bad:
git commit -m "feat: add comprehensive conversation memory management system with caching"

# 4. Separate subject from body with blank line
git commit -m "feat: implement proactive engagement engine

The proactive engagement engine analyzes user behavior patterns
and triggers appropriate interventions to maintain engagement
and prevent abandonment.

- Add behavior analysis algorithms
- Implement trigger condition evaluation
- Add message scheduling system
- Include comprehensive test coverage

Closes #789"
```

## Pull Request Process

### Pull Request Template
```markdown
## Description
Brief description of the changes and their purpose.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Related Issues
Closes #[issue_number]
Related to #[issue_number]

## Changes Made
- [ ] Change 1
- [ ] Change 2
- [ ] Change 3

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] All tests pass

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Checklist
- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
```

### Review Process
```bash
# 1. Create pull request
# - Use descriptive title
# - Fill out PR template completely
# - Assign appropriate reviewers
# - Add relevant labels

# 2. Automated checks
# - All CI/CD pipelines must pass
# - Code coverage must meet minimum threshold
# - Security scans must pass
# - Linting and formatting checks must pass

# 3. Code review requirements
# - At least 2 approvals for main/develop branches
# - At least 1 approval for feature branches
# - Security team approval for security-related changes
# - Architecture team approval for major architectural changes

# 4. Merge strategies
# - Squash and merge for feature branches (clean history)
# - Merge commit for release branches (preserve branch history)
# - Rebase and merge for small fixes (linear history)
```

### Review Guidelines
```markdown
## For Authors
- [ ] Self-review your code before requesting review
- [ ] Ensure all tests pass and coverage is adequate
- [ ] Update documentation as needed
- [ ] Respond to review comments promptly
- [ ] Keep PRs focused and reasonably sized (<500 lines when possible)

## For Reviewers
- [ ] Review code for correctness, readability, and maintainability
- [ ] Check for security vulnerabilities
- [ ] Verify tests are comprehensive and meaningful
- [ ] Ensure documentation is updated
- [ ] Provide constructive feedback
- [ ] Approve only when confident in the changes
```

## Release Management

### Semantic Versioning
We follow [Semantic Versioning](https://semver.org/) (SemVer):

```
MAJOR.MINOR.PATCH

Examples:
1.0.0 - Initial release
1.1.0 - New features, backward compatible
1.1.1 - Bug fixes, backward compatible
2.0.0 - Breaking changes
```

### Version Bumping Strategy
```bash
# Patch version (1.1.0 → 1.1.1)
# - Bug fixes
# - Security patches
# - Documentation updates

# Minor version (1.1.1 → 1.2.0)
# - New features
# - New API endpoints
# - Performance improvements
# - Deprecations (with backward compatibility)

# Major version (1.2.0 → 2.0.0)
# - Breaking API changes
# - Removed deprecated features
# - Major architectural changes
# - Database schema breaking changes
```

### Release Process
```bash
# 1. Prepare release branch
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0

# 2. Update version numbers
# - package.json (frontend)
# - pyproject.toml (backend)
# - version.py or __init__.py
# - API version constants

# 3. Update changelog
# Add new version section to CHANGELOG.md
# List all features, fixes, and breaking changes

# 4. Run final tests
npm run test:all
pytest --cov=app tests/
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# 5. Create release commit
git add .
git commit -m "chore(release): prepare v1.2.0

- Bump version to 1.2.0
- Update changelog
- Final testing completed"

# 6. Merge to main and tag
git checkout main
git merge --no-ff release/v1.2.0
git tag -a v1.2.0 -m "Release v1.2.0

Features:
- AI conversation engine improvements
- Mobile app push notifications
- Enhanced user analytics

Bug fixes:
- Fixed memory leak in conversation manager
- Resolved mobile app crash on startup

Breaking changes:
- Updated API authentication format"

# 7. Merge back to develop
git checkout develop
git merge --no-ff release/v1.2.0

# 8. Push everything
git push origin main
git push origin develop
git push origin v1.2.0

# 9. Clean up
git branch -d release/v1.2.0
git push origin --delete release/v1.2.0

# 10. Create GitHub release
# Use GitHub interface or CLI to create release notes
```

### Hotfix Process
```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-patch

# 2. Make the fix
git commit -m "fix: patch critical security vulnerability

- Update authentication validation
- Add input sanitization
- Increase security test coverage

CVE-2024-XXXX"

# 3. Test thoroughly
npm run test:security
pytest tests/security/

# 4. Bump patch version
# Update version to 1.2.1

# 5. Merge to main and develop
git checkout main
git merge --no-ff hotfix/critical-security-patch
git tag -a v1.2.1 -m "Hotfix v1.2.1 - Security patch"

git checkout develop
git merge --no-ff hotfix/critical-security-patch

# 6. Push and clean up
git push origin main
git push origin develop
git push origin v1.2.1
git branch -d hotfix/critical-security-patch
```

## Git Configuration

### Global Git Configuration
```bash
# Set up user information
git config --global user.name "Your Name"
git config --global user.email "your.email@company.com"

# Set up default branch name
git config --global init.defaultBranch main

# Set up pull strategy
git config --global pull.rebase false

# Set up push strategy
git config --global push.default simple

# Enable helpful colors
git config --global color.ui auto

# Set up aliases
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual '!gitk'
git config --global alias.graph 'log --oneline --graph --decorate --all'
```

### Repository-specific Configuration
```bash
# .gitconfig (in repository root)
[core]
    autocrlf = input
    safecrlf = true
    editor = code --wait

[merge]
    tool = vscode

[mergetool "vscode"]
    cmd = code --wait $MERGED

[diff]
    tool = vscode

[difftool "vscode"]
    cmd = code --wait --diff $LOCAL $REMOTE
```

### .gitignore Template
```gitignore
# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
pip-log.txt
pip-delete-this-directory.txt

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Build outputs
dist/
build/
*.egg-info/
.coverage
htmlcov/
.pytest_cache/
.mypy_cache/

# Logs
*.log
logs/

# Database
*.db
*.sqlite3

# Docker
.dockerignore

# Temporary files
*.tmp
*.temp
.cache/
```

## Automation and Hooks

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0-alpha.4
    hooks:
      - id: prettier
        types_or: [javascript, jsx, ts, tsx, json, yaml, markdown]
```

### GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install Python dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Install Node.js dependencies
      run: npm ci
    
    - name: Run Python tests
      run: pytest --cov=app tests/
    
    - name: Run JavaScript tests
      run: npm test
    
    - name: Run linting
      run: |
        flake8 app/
        npm run lint
    
    - name: Build application
      run: |
        npm run build
        docker build -t coaching-platform .
```

This comprehensive Git workflow ensures consistent development practices, maintains code quality, and supports efficient collaboration across the development team.