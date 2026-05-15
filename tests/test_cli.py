from pipedoctor.cli import main


def test_demo_cli_runs_json(capsys):
    code = main(["demo", "--format", "json"])
    captured = capsys.readouterr()

    assert code == 0
    assert '"name": "demo_orders"' in captured.out
