from markwise.services.roster import read_table, rows_from_table


def test_leading_zeros_and_duplicates(tmp_path):
    f = tmp_path / "roster.csv"
    f.write_text("ID,Name,Consent\n0045123,Ali,yes\n0045124,Sara,no\n0045123,Dup,yes\n,Blank,yes\n",
                 encoding="utf-8")
    rows, duplicates = rows_from_table(read_table(str(f)), "ID", "Name", None, "Consent")
    assert [r["student_id"] for r in rows] == ["0045123", "0045124"]
    assert duplicates == ["0045123"]
    assert rows[0]["consent"] is True and rows[1]["consent"] is False


def test_excel_file(tmp_path):
    import pandas as pd

    f = tmp_path / "roster.xlsx"
    pd.DataFrame({"Roll No": ["0001", "0002"], "Student Name": ["A", "B"]}).to_excel(f, index=False)
    rows, _ = rows_from_table(read_table(str(f)), "Roll No", "Student Name", default_consent=True)
    assert rows[0]["student_id"] == "0001" and rows[0]["consent"] is True
