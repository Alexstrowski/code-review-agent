from operator import add
from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, Field, model_validator


class Finding(BaseModel):
    category: Literal["bug", "security", "standards"]
    line_start: int = Field(description="first line of the issue (1-indexed)")
    line_end: int
    severity: Literal["low", "medium", "high"]
    message: str = Field(description="what is wrong and how to fix it")


class Review(BaseModel):
    findings: list[Finding] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce_shape(cls, data):
        # weak models sometimes return a bare list instead of {"findings": [...]}
        if isinstance(data, list):
            return {"findings": data}
        return data


class ReviewState(TypedDict):
    code: str
    findings: Annotated[list[Finding], add]
    verified: list[Finding]
