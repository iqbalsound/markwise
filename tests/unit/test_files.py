from markwise.services.files import list_pdfs, make_zip, match_pdf


def test_matching_and_zip(tmp_path):
    for name in ("0045123_Ali.pdf", "ID45123.pdf", "notes.txt"):
        (tmp_path / name).write_bytes(b"x")
    pdfs = list_pdfs(tmp_path)
    assert [p.name for p in pdfs] == ["0045123_Ali.pdf", "ID45123.pdf"]
    assert match_pdf("0045123", pdfs).name == "0045123_Ali.pdf"
    assert match_pdf("45123", pdfs) is None        # must not match inside a longer ID
    assert match_pdf("999", pdfs) is None
    assert make_zip(pdfs, tmp_path / "out.zip") == 2
