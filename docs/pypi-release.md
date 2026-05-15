# PyPI Release

1. Update the version in `pyproject.toml`.
2. Run tests:

```bash
pytest
```

3. Build:

```bash
python -m build
```

4. Check the package:

```bash
python -m twine check dist/*
```

5. Upload to TestPyPI first:

```bash
python -m twine upload --repository testpypi dist/*
```

6. Upload to PyPI:

```bash
python -m twine upload dist/*
```

Recommended release flow for maintainers:

- tag releases as `v0.1.0`
- keep release notes short and example-led
- publish one notebook screenshot per release
- include at least one new "good first issue" after every release
