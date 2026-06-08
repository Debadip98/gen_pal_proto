"""Export a question bank to downloadable bytes (Excel and CSV).

Each question is a dict with "question", "answer", and "difficulty" keys.
Functions return raw bytes suitable for st.download_button.
"""

from __future__ import annotations

import csv
import io

from openpyxl import Workbook

_HEADERS = ("#", "Question", "Answer", "Difficulty")


def _rows(questions: list[dict]):
    for i, q in enumerate(questions, start=1):
        yield (
            i,
            str(q.get("question", "")),
            str(q.get("answer", "")),
            str(q.get("difficulty", "")),
        )


def to_xlsx_bytes(questions: list[dict]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Questions"
    sheet.append(_HEADERS)
    for row in _rows(questions):
        sheet.append(row)

    widths = (5, 70, 70, 12)
    for column_index, width in enumerate(widths, start=1):
        sheet.column_dimensions[chr(64 + column_index)].width = width

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def to_csv_bytes(questions: list[dict]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_HEADERS)
    writer.writerows(_rows(questions))
    return buffer.getvalue().encode("utf-8-sig")
