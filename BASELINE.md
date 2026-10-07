# Baseline of master at 4c90ed511d0a

The proposed gate, run on the default branch as it is, before any Run changes it.

| Command | Result | Seconds |
|---|---|---|
| `$python -m black --check --quiet src tests` | passes | 5.8 |
| `$python -m isort --check-only src tests` | passes | 2.4 |
| `$python -m flake8 src tests` | passes | 8.6 |
| `$python -m mypy --disable-error-code redundant-cast` | passes | 27.7 |
| `$python -c "import os, sys, pytest; os.environ['PATH'] = os.path.dirname(sys.executable) + os.pathsep + os.environ['PATH']; os.environ['MYPYPATH']=os.path.abspath('src'); raise SystemExit(pytest.main(['-q', '-o', 'pythonpath=src', '--mypy-ini-file=setup.cfg', '--mypy-only-local-stub', '--deselect', 'tests/test_moneyed_classes.py::test_all_babel_currencies']))"` | passes | 61.5 |

Installed first: `$python -m pip install --upgrade pip`, `$python -m pip install "babel>=2.8.0" "typing-extensions>=3.7.4.3"`, `$python -m pip install "pytest==8.1.1" "pytest-mypy-plugins==3.1.0" "mypy==1.9.0"`, `$python -m pip install "black==24.4.0" "isort==5.13.2" "flake8==7.0.0" flake8-type-checking flake8-bugbear flake8-comprehensions flake8-print flake8-mutable flake8-simplify flake8-pytest-style flake8-printf-formatting`
