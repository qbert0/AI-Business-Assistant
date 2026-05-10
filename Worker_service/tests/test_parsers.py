from deepdoc.parsers import ParsedDocument, TxtParser, create_parser


def test_txt_parser_parses_utf8_text() -> None:
    parser = TxtParser()

    result = parser.parse_bytes("xin chao".encode("utf-8"), "sample.txt")

    assert isinstance(result, ParsedDocument)
    assert result.text == "xin chao"
    assert result.markdown == "xin chao"
    assert result.parser_name == "txt"


def test_create_parser_returns_expected_parser_types() -> None:
    assert create_parser("a.txt").name == "txt"
    assert create_parser("a.pdf").name == "pdf"
    assert create_parser("a.docx").name == "docx"
    assert create_parser("a.xlsx").name == "xlsx"
