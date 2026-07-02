from pydantic import BaseModel


class ImportFileResult(BaseModel):
    filename: str
    status: str  # success | partial | failed
    rows_imported: int
    errors: list[str] = []


class ImportSummary(BaseModel):
    files: list[ImportFileResult]
    total_messages_imported: int
    total_posts_imported: int
    total_connections_imported: int
