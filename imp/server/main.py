import sqlite3
import json
import tornado.ioloop
import tornado.web


class Handler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

# TODO:
# https://imgur.com/gallery/IaHuZ
class ListImageHandler(Handler):
    def get(self):
        images = self.db.execute("SELECT key, name FROM images;")
        self.render('image_list.html', images=images.fetchmany(30))


class ShowImageHandler(Handler):
    def get(self, image_key):
        image = self.db.execute('SELECT * FROM images WHERE key = ?',
                                [image_key])
        if image is None:
            self.write("Image not found")
        else:
            data = image.fetchone()
            tags = self.db.execute('SELECT tags.name FROM image_tags '
                                   'INNER JOIN tags ON tags.id = tag_id '
                                   'WHERE image_id = ?', [data['id']])
            self.render('image_show.html', name=data['name'],
                        desc=data['description'], url=data['url'],
                        tags=tags.fetchall())


class NewImageHandler(Handler):
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


class ImageTagsHandler(Handler):
    def get(self, image_key):
        self.set_header("Content-Type", "text/json")
        image_id = self.db.execute('SELECT id FROM images WHERE key = ?',
                                   [image_key]).fetchone()
        if image_id is None:
            self.set_status(404)
            return

        image_id = image_id[0]
        tags = self.db.execute('SELECT tags.name FROM image_tags '
                               'INNER JOIN tags ON tags.id = tag_id '
                               'WHERE image_id = ?', [image_id])
        output = json.dumps([tag['name'] for tag in tags.fetchall()])
        self.write(output)


class ListTagHandler(Handler):
    def get(self):
        tags = self.db.execute('SELECT name FROM tags').fetchmany(100)
        self.render('tags_list.html', tags=tags)


class ViewTagHandler(Handler):
    def get(self, tag_name):
        tag_name = tag_name.replace('+', ' ')
        tag = self.db.execute('SELECT * FROM tags WHERE name = ?',
                              [tag_name]).fetchone()

        if tag is None:
            self.set_status(404)
            return

        images = self.db.execute('SELECT images.key, images.name FROM image_tags '
                                 'INNER JOIN images ON images.id = image_id '
                                 'WHERE tag_id = ?', [tag['id']]).fetchmany(100)
        self.render('tags_view.html', name=tag_name, images=images)


def make_app(db):
    db = {'db': db}
    return tornado.web.Application([
        (r'/', ListImageHandler, db),
        (r'/images/?', ListImageHandler, db),
        (r'/images/new', NewImageHandler, db),
        (r'/images/([^/]+)', ShowImageHandler, db),
        (r'/images/([^/]+)/tags.json', ImageTagsHandler, db),
        (r'/tags/?', ListTagHandler, db),
        (r'/tags/([^/]+)', ViewTagHandler, db),
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
