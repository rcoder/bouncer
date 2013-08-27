# Copyright 2013 by Urban Airship and Lennon Day-Reynolds <lennon@urbanairship.com>
# See license information in COPYING.

from contextlib import contextmanager
from pkg_resources import resource_string

import os
import sqlite3

# Database helper functions (we don't need no steenkin' ORM!)

@contextmanager
def dbopen():
  db_path = os.environ.get('BOUNCER_DB_PATH', './bouncer.db')
  db = sqlite3.connect(db_path)
  try:
    yield db
  finally:
    db.close()

@contextmanager
def dbcursor(db):
  c = db.cursor()
  try:
    yield c
  finally:
    c.close()

@contextmanager
def q(q, *params):
  'Perform a DB query, yield the active cursor, then commit'
  with dbopen() as db, dbcursor(db) as c:
    c.execute(q, params)
    yield c
    db.commit()

def iq(q, *params):
  'Execute a query, commit, and return the last insert row'
  with dbopen() as db, dbcursor(db) as c:
    rowid = None
    c.execute(q, params)
    db.commit()
    rowid = c.lastrowid
  return rowid

# Keep the schema inline, so we can drop it into the database at any time
SCHEMA_DDL = '''
drop table if exists urls;

create table urls (
  slug text unique,
  full_url text,
  clicks int default 0,
  ctime timestamp default current_timestamp,
  atime timestamp default current_timestamp
);
'''

def initdb():
  with dbopen() as db:
    db.executescript(SCHEMA_DDL)

