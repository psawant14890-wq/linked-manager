from app.services.linkedin_parser import parse_connections_csv, parse_messages_csv, parse_shares_csv


def test_parse_messages_csv_happy_path():
    raw = b"FROM,DATE,CONTENT\nJane Doe,01/15/24, 09:00 AM,Hey -- loved your last post!\n"
    result = parse_messages_csv(raw)
    assert result.status in ("success", "partial")
    assert result.rows_imported >= 1
    assert result.messages[0].sender_name == "Jane Doe"


def test_parse_messages_csv_skips_rows_missing_content():
    raw = b"FROM,DATE,CONTENT\nJane Doe,01/15/24,\nJohn Smith,01/16/24,Real message here\n"
    result = parse_messages_csv(raw)
    assert result.rows_imported == 1
    assert len(result.errors) == 1
    assert result.status == "partial"


def test_parse_messages_csv_empty_file_fails():
    result = parse_messages_csv(b"")
    assert result.status == "failed"
    assert result.rows_imported == 0


def test_parse_shares_csv_happy_path():
    raw = b"Date,ShareCommentary\n2024-03-01,Excited to announce our new release!\n"
    result = parse_shares_csv(raw)
    assert result.rows_imported == 1
    assert "Excited" in result.posts[0].content


def test_parse_connections_csv_handles_preamble_lines():
    raw = (
        b"Notes:\n"
        b"This file contains your connections.\n"
        b"\n"
        b"First Name,Last Name,Company,Position,Connected On\n"
        b"Alex,Rivera,Acme Corp,Engineering Manager,15 Jan 2024\n"
    )
    result = parse_connections_csv(raw)
    assert result.rows_imported == 1
    assert result.connections[0].name == "Alex Rivera"
    assert result.connections[0].company == "Acme Corp"


def test_parse_connections_csv_missing_header_fails():
    result = parse_connections_csv(b"garbage,data\n1,2\n")
    assert result.status == "failed"
