import sqlite3
import json
import tornado.ioloop
import tornado.web


# TODO:
# https://imgur.com/gallery/IaHuZ
class ListImageHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    def get(self):
        images = self.db.execute("SELECT key, name FROM images;")
        self.render('image_list.html', images=images.fetchmany(30))
            

class ShowImageHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    def get(self, image_id):
        image = self.db.execute('SELECT * FROM images WHERE key = ?',
                                [image_id])
        if image is None:
            self.write("Image not found")
        else:
            data = image.fetchone()
            self.render('image_show.html', name=data['name'],
                        desc=data['description'], url=data['url'])


class NewImageHandler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    def get(self):
        self.render('image_form.html')

    def post(self):
        self.set_header("Content-Type", "text/plain")
        name = self.get_body_argument("name")
        url = self.get_body_argument("url")
        description = self.get_body_argument("description")
        image = url.split('/')[-1]
        key = image.split('.')[0]
        if not description:
            description = None
        with self.db:
            self.db.execute(
                'INSERT INTO images (name, key, url, description) '
                'VALUES (?, ?, ?, ?)', (name, key, url, description))
        self.redirect('/images/{}'.format(key))


def make_app(db):
    return tornado.web.Application([
        (r'/', ListImageHandler, {'db': db}),
        (r'/images/', ListImageHandler, {'db': db}),
        (r'/images/new', NewImageHandler, {'db': db}),
        (r'/images/([^/]+)', ShowImageHandler, {'db': db}),
    ], debug=True)


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


if __name__ == '__main__':
    db = make_db()
    app = make_app(db)
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
