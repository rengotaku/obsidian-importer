# Research: GitHub Actions Lint CI

**Feature**: 061-github-actions-lint
**Date**: 2026-02-24

## Research Tasks

1. GitHub Actions best practices for Python linting
2. pylint configuration for Kedro projects
3. pip cache strategy in GitHub Actions
4. Version pinning strategy

---

## 1. GitHub Actions Best Practices

### Decision
`actions/setup-python@v5` + built-in cache option

### Rationale
- `actions/setup-python@v5` has built-in `cache: 'pip'` option
- Uses pyproject.toml hash as cache key automatically
- No need for separate `actions/cache` action

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| `pip-tools` lock file | Overkill for this project |
| Docker container | Longer setup time |
| `actions/cache` separately | Redundant with built-in option |

### Best Practice References
- GitHub Actions Python workflow: https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python
- setup-python action: https://github.com/actions/setup-python

---

## 2. pylint Configuration

### Decision
Add `[tool.pylint]` section to pyproject.toml

### Rationale
- Single source of truth with ruff config
- Modern Python packaging standard
- No additional config files needed

### Recommended Settings
```toml
[tool.pylint.main]
ignore = [".venv", "venv", "__pycache__", ".staging", ".specify", ".claude"]
jobs = 0  # auto-detect CPU count

[tool.pylint.messages_control]
disable = [
    "C0114",  # missing-module-docstring (ruff handles)
    "C0115",  # missing-class-docstring
    "C0116",  # missing-function-docstring
    "W0511",  # fixme (allow TODO comments)
    "R0903",  # too-few-public-methods
]

[tool.pylint.format]
max-line-length = 100  # match ruff setting
```

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| `.pylintrc` file | Config file proliferation |
| `setup.cfg` | Deprecated for modern Python |

---

## 3. pip Cache Strategy

### Decision
Use `actions/setup-python` built-in `cache: 'pip'` option

### Rationale
- Zero additional configuration
- Automatic cache key from pyproject.toml hash
- Automatic fallback on cache miss
- Well-maintained by GitHub

### Implementation
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'
```

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| `actions/cache` direct | Redundant, more config |
| No cache | Slow CI (~2min install every time) |
| pip cache directory only | Less reliable |

---

## 4. Version Pinning Strategy

### Decision
Pin exact versions in pyproject.toml

### Current State (to fix)
```toml
# Current - range specified
"ruff>=0.1.0"

# Target - exact version
"ruff==0.8.6"
"pylint==3.3.3"
```

### Rationale
- Guarantees identical versions between local and CI
- Prevents unexpected version upgrades breaking CI
- Clear upgrade path when needed

### Version Selection
- **ruff**: Check latest stable at https://pypi.org/project/ruff/
- **pylint**: Check latest stable at https://pypi.org/project/pylint/

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|--------------|
| Range specifiers | Version drift between local/CI |
| Lock file | Overkill, adds complexity |

---

## Summary

All research items resolved. No NEEDS CLARIFICATION remaining.

| Item | Decision |
|------|----------|
| CI Framework | GitHub Actions with setup-python@v5 |
| Cache Strategy | Built-in pip cache |
| pylint Config | pyproject.toml `[tool.pylint]` |
| Version Management | Exact pinning in pyproject.toml |
