import sqlite3
import logging
import shutil

logger = logging.getLogger(__name__)


def database_0_to_1(db):
    with db:
        db.executescript('''\
CREATE TABLE images (
    id INTEGER PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    key VARCHAR(24) NOT NULL,
    url TEXT NOT NULL,
    file TEXT,
    description TEXT
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY NOT NULL,
    name VARCHAR(64) UNIQUE NOT NULL
);

CREATE TABLE image_tags (
    id INTEGER PRIMARY KEY NOT NULL,
    image_id INTEGER NOT NULL REFERENCES images(id) ON UPDATE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON UPDATE CASCADE
);''')
        db.execute('PRAGMA user_version = 1;')


def database_1_to_2(db):
    with db:
        db.executescript('''\
CREATE TABLE categories (
    id INTEGER PRIMARY KEY NOT NULL,
    name VARCHAR(64) UNIQUE NOT NULL
);

ALTER TABLE tags RENAME TO tags_old;

CREATE TABLE tags (
    id INTEGER PRIMARY KEY NOT NULL,
    name VARCHAR(64) UNIQUE NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON UPDATE CASCADE
);

INSERT INTO tags (id, name) SELECT id, name FROM tags_old;''')
        db.execute('PRAGMA user_version = 2;')


db_upgrades = [database_0_to_1, database_1_to_2]


def make_db(name):
    con = sqlite3.connect(name)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON;')
    version = con.execute('PRAGMA user_version;').fetchone()[0]
    if version > len(db_upgrades):
        version_message = ('Error, database version {}, maximum '
                           'supported version is {}.'.format(
                               version, len(db_upgrades)))
        raise Exception(version_message)

    # Save a backup, eg imp.db.2
    # This will only save a backup for the first upgrade, so if you have
    # a database on version 2, and it needs to be upgraded to version 5,
    # then you will get a backup (such as imp.db.2) but no imp.db.3 or
    # imp.db.4
    # We don't take a backup of the zero version database, because it can't
    # contain any well-formed content.
    if version < len(db_upgrades) and version > 0:
        shutil.copy2(name, name + '.' + str(version))
    while version < len(db_upgrades):
        upgrade = db_upgrades[version]
        upgrade(con)
        old_version = version
        version = con.execute('PRAGMA user_version;').fetchone()[0]
        logger.info("Upgraded schema from user version %d to %d",
                    old_version, version)
    return con
