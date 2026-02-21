from app.services.value_parser import parse_value


def test_parse_none_and_na():
    assert parse_value(None) is None
    assert parse_value("") is None
    assert parse_value("N/A") is None
    assert parse_value("-") is None


def test_parse_commas():
    assert parse_value("1,234.56") == 1234.56
    assert parse_value("4,560") == 4560.0


def test_parse_percent():
    assert parse_value("45%") == 0.45
    assert parse_value("(45%)") == -0.45


def test_parse_yes_no():
    assert parse_value("YES") == 1.0
    assert parse_value("no") == 0.0


def test_parse_parentheses_negative():
    assert parse_value("(123.4)") == -123.4

