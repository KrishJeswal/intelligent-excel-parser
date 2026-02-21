from app.services.header_detector import detect_header_row


def test_detect_header_row_skips_title():
    rows = [
        ["Monthly Report"], 
        [None],
        ["Date", "Coal Consump (AFBC-1)", "Pwr Gen (TG-1)"],
        ["2026-02-20", "1,234.56", "85.2"]
    ]
    idx, headers, warnings = detect_header_row(rows)
    assert idx == 2
    assert headers[0] == "Date"
    assert any("title row" in w.lower() for w in warnings)

