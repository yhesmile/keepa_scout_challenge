from app.services.sql_guard import validate_select_sql


def test_validate_select_sql_accepts_single_select() -> None:
    assert validate_select_sql('SELECT * FROM asins WHERE eligible = 1') is True



def test_validate_select_sql_rejects_destructive_sql() -> None:
    assert validate_select_sql('SELECT * FROM asins; DROP TABLE asins') is False
