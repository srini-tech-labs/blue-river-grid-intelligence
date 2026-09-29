from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .services.knowledge import DOCUMENT_TYPES, MAX_RESULTS

DocumentType = Literal[DOCUMENT_TYPES]  # type: ignore[valid-type]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class KnowledgeSearchRequest(_Strict):
    query: str = Field(min_length=2, max_length=500)
    asset_id: str | None = Field(default=None, max_length=16)
    document_type: DocumentType | None = None
    num_results: int = Field(default=8, ge=1, le=MAX_RESULTS)

    @field_validator("asset_id")
    @classmethod
    def _blank_is_none(cls, v):
        return v or None


class OperationsIntelligenceRequest(_Strict):
    question: str = Field(min_length=3, max_length=1000)
    asset_id: str | None = Field(default=None, max_length=16)

    @field_validator("asset_id")
    @classmethod
    def _blank_is_none(cls, v):
        return v or None
