import csv
import hashlib
import io
import uuid
from dataclasses import dataclass

CSV_COLUMNS = (
    "public_id",
    "card_id",
    "card_version_id",
    "front_text",
    "back_text",
    "answer_text",
    "explanation_text",
    "tags",
)


@dataclass(frozen=True)
class ReleaseCsvRow:
    public_id: str
    card_id: uuid.UUID
    card_version_id: uuid.UUID
    front_text: str
    back_text: str
    answer_text: str
    explanation_text: str
    tags: str


@dataclass(frozen=True)
class CsvExport:
    content: bytes
    sha256: str
    row_count: int


def build_release_csv(
    rows: list[ReleaseCsvRow],
    *,
    delimiter: str,
) -> CsvExport:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=CSV_COLUMNS,
        delimiter=delimiter,
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writeheader()
    for row in sorted(rows, key=lambda item: (item.public_id, str(item.card_id))):
        writer.writerow(
            {
                "public_id": row.public_id,
                "card_id": str(row.card_id),
                "card_version_id": str(row.card_version_id),
                "front_text": row.front_text,
                "back_text": row.back_text,
                "answer_text": row.answer_text,
                "explanation_text": row.explanation_text,
                "tags": row.tags,
            }
        )

    content = output.getvalue().encode("utf-8")
    return CsvExport(
        content=content,
        sha256=hashlib.sha256(content).hexdigest(),
        row_count=len(rows),
    )
