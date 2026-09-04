from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    """Strict, immutable base for versioned system-boundary contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


def require_utc(value: datetime) -> datetime:
    """Reject naive and non-UTC timestamps at system boundaries."""

    offset = value.utcoffset()
    if value.tzinfo is None or offset is None:
        raise ValueError("timestamp must include UTC timezone information")
    if offset.total_seconds() != 0:
        raise ValueError("timestamp must be normalized to UTC")
    return value
