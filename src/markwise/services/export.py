import pandas as pd

COLUMNS = [
    "Student ID", "Name", "PDF file", "Status", "Score",
    "Max marks", "Confidence", "Feedback", "Edited by teacher",
]


def export_rows(rows, path: str) -> None:
    df = pd.DataFrame(rows, columns=COLUMNS)
    if path.lower().endswith(".csv"):
        df.to_csv(path, index=False, encoding="utf-8-sig")  # utf-8-sig so Excel opens it correctly
    else:
        df.to_excel(path, index=False)
