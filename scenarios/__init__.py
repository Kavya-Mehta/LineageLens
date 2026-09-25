"""Failure scenarios registry."""

from . import (
    nothing_wrong,
    schema_changed,
    silent_nulls,
    unanswerable,
    upstream_failed,
)

REGISTRY = {
    module.NAME: module
    for module in (
        upstream_failed,
        schema_changed,
        silent_nulls,
        nothing_wrong,
        unanswerable,
    )
}

__all__ = ["REGISTRY"]