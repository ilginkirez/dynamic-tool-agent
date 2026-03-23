"""Pydantic v2 models for Tool Registry system."""

from pydantic import BaseModel


class ToolParameter(BaseModel):
    """Describes a single parameter that a tool accepts."""

    name: str
    type: str  # "string", "number", "boolean"
    description: str
    required: bool = True


class ToolVersion(BaseModel):
    """Semantic version representation for a tool."""

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


class ToolSchema(BaseModel):
    """
    Complete schema definition for a registered tool.

    The `callable_template` field is inspired by the AutoTools paper:
    the LLM reads the tool documentation and encapsulates the tool as a
    callable function. This reduces prompt-injection risk because the LLM
    fills in a structured template instead of generating free-form code.
    """

    name: str  # snake_case identifier, e.g. weather_service
    display_name: str
    description: str  # rich description for semantic search
    category: str  # "data", "utility", "communication", "computation"
    tags: list[str]
    parameters: list[ToolParameter]
    version: ToolVersion
    deprecated: bool = False
    replaced_by: str | None = None
    examples: list[str]  # at least 2 example usage scenarios
    callable_template: str  # minimal Python call template
