import os
import sqlite3
from flask import g

ENV = os.getenv("FLASK_ENV", "development")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def sql_param():
    return "%s" if ENV == "production" else "?"

def get_db():
    if "db" not in g:
        if ENV == "production":
            import psycopg2
            from psycopg2.extras import RealDictCursor

            g.db = psycopg2.connect(
                os.getenv("DATABASE_URL"),
                cursor_factory=RealDictCursor
            )
        else:
            db_path = os.path.join(BASE_DIR, "setup/app.db")
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON;")

    return g.db

def execute(db, sql, params=()):
    if ENV == "production":
        cur = db.cursor()
        cur.execute(sql, params)
        return cur
    else:
        return db.execute(sql, params)