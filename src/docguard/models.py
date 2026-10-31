
from typing import Literal

from pydantic import BaseModel, Field


class Claim(BaseModel):
    text: str
    file_path: str
    line_number: int = Field(ge=1)
    value: str | None = None


class Fact(BaseModel):
    text: str
    file_path: str
    line_number: int = Field(ge=1)
    value: str | None = None


class Finding(BaseModel):
    rule_id: str
    title: str
    message: str
    confidence: Literal["high", "medium", "low"] = "medium"

    documentation_file: str
    documentation_line: int = Field(ge=1)
    documented_text: str

    evidence_file: str | None = None
    evidence_line: int | None = Field(default=None, ge=1)
    evidence_text: str | None = None

    suggested_fix: str | None = None
