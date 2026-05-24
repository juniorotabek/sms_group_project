from smart_warehouse_robot.cli import format_table


def test_format_table_returns_readable_table():
    table = format_table(
        rows=[
            {"Name": "Member 1", "Role": "Task Management"},
            {"Name": "Member 2", "Role": "Navigation"},
        ],
        columns=["Name", "Role"],
    )
    assert "Name" in table
    assert "Role" in table
    assert "Member 1" in table
    assert "|" in table
