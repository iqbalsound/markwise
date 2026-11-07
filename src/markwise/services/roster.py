import pandas as pd

TRUE_WORDS = {"yes", "y", "true", "t", "1", "agreed", "consented"}


def read_table(path: str) -> pd.DataFrame:
    """Read a .csv or Excel file with every cell as text (keeps leading zeros)."""
    if path.lower().endswith(".csv"):
        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig", keep_default_na=False)
    else:
        df = pd.read_excel(path, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def guess_column(columns, keywords):
    for column in columns:
        low = column.lower().replace("_", " ")
        if any(k in low for k in keywords):
            return column
    return None


def rows_from_table(df, id_col, name_col, email_col=None, consent_col=None, default_consent=False):
    """Return (rows, duplicate_ids). Each row: student_id, name, email, consent."""
    rows, duplicates, seen = [], [], set()
    for _, record in df.iterrows():
        sid = str(record[id_col]).strip()
        if sid.endswith(".0") and sid[:-2].isdigit():  # Excel number stored as float
            sid = sid[:-2]
        if not sid or sid.lower() == "nan":
            continue
        if sid in seen:
            duplicates.append(sid)
            continue
        seen.add(sid)
        consent = default_consent
        if consent_col:
            consent = str(record[consent_col]).strip().lower() in TRUE_WORDS
        rows.append(
            {
                "student_id": sid,
                "name": str(record[name_col]).strip(),
                "email": str(record[email_col]).strip() if email_col else "",
                "consent": consent,
            }
        )
    return rows, duplicates
