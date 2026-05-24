from smart_warehouse_robot.cli import main


def test_cli_module_smoke_imports():
    assert main is not None
