import pytest
from anki_ocr.utils import format_note_id_query
NOTE_ID_QUERY_EXPECTED = [
    ([1601851621708, 1601851571572], "nid:1601851621708 OR nid:1601851571572"),
    ([1601851621708], "nid:1601851621708")
]
@pytest.mark.parametrize(["note_ids", "expected"], NOTE_ID_QUERY_EXPECTED)
def test_format_note_id_query(note_ids, expected):
    output = format_note_id_query(note_ids=note_ids)
    assert output == expected
