from .db_main import Database


_db = Database()
Base = _db.Base


__all__ = ["_db", "Base"]
