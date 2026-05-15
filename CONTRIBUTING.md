# Contributing

Thanks for considering a contribution to PipeDoctor.

The best first contributions are small, useful, and easy to review:

- add a detector with two tests
- improve a recommendation message
- add an example notebook or screenshot
- add a new export format
- improve Spark plan parsing
- add a Polars or DuckDB adapter

## Local Setup

```bash
git clone https://github.com/ravikiranpagidi/pipedoctor.git
cd pipedoctor
pip install -e ".[dev]"
pytest
```

## Rule Guidelines

Good rules should:

- explain why the issue matters
- show evidence
- recommend a safe next action
- avoid claiming certainty when the signal is only a heuristic
- run quickly on notebook-sized data

## Pull Request Checklist

- tests pass
- README or docs updated if behavior changes
- no new heavy dependencies without discussion
- findings include evidence and recommendations
