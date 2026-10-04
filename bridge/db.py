"""Small SQLite data layer; each process opens its own connection."""
import sqlite3
from pathlib import Path
from flask import current_app, g

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'], timeout=30)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db

def close_db(_error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript(Path(__file__).with_name('schema.sql').read_text())
    db.execute('BEGIN IMMEDIATE')
    columns = {row['name'] for row in db.execute('PRAGMA table_info(tasks)')}
    if 'details' not in columns:
        db.execute("ALTER TABLE tasks ADD COLUMN details TEXT NOT NULL DEFAULT '{}'")
    db.commit()
