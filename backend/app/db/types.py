"""Custom SQLAlchemy types (e.g. for SQLite boolean string handling)."""
from sqlalchemy import Boolean
from sqlalchemy.types import TypeDecorator


class BooleanCoerce(TypeDecorator[bool]):
    """Boolean that normalizes SQLite string 'false'/'true' to bool.

    In SQLite, server_default='false' can store the string "false".
    Python's bool("false") is True (non-empty string), so raw Boolean
    would wrongly return True. This type coerces "false"/"true" on read.
    """

    impl = Boolean
    cache_ok = True

    def process_result_value(self, value: object, dialect: object) -> bool | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)
