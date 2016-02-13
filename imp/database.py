import sqlite3


def make_db():
    con = sqlite3.connect('imp.db')
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON;')
    data = con.execute('PRAGMA user_version;')
    version = data.fetchone()[0]
    if version == 0:
        with con:
            con.executescript('''
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
            );
            ''')
            con.execute('PRAGMA user_version = 1;')
    return con
