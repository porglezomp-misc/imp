import sqlite3
import json
import tornado.ioloop
import tornado.web
import database


class Handler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db


class ListImageHandler(Handler):
    def get(self):
        images = self.db.execute("SELECT key, name FROM images;")
        self.render('images/index.html', images=images.fetchall())


class ListImageJSON(Handler):
    def get(self):
        self.set_header("Content-Type", "text/json")
        images = self.db.execute("SELECT * FROM images")
        entries = [{'key': img['key'], 'name': img['name']}
                   for img in images.fetchall()]
        out = json.dumps(entries)
        self.write(out)


class ShowImageHandler(Handler):
    def get(self, image_key):
        image = self.db.execute('SELECT * FROM images WHERE key = ?',
                                [image_key]).fetchone()
        if image is None:
            self.set_status(404)
            self.write('image not found')
            return

        tags = self.db.execute('SELECT tags.name FROM image_tags '
                               'INNER JOIN tags ON tags.id = tag_id '
                               'WHERE image_id = ?', [image['id']])

        if image['file'] is None:
            url = image['url']
        else:
            url = '/static/' + image['file']

        self.render('images/show.html', name=image['name'],
                    desc=image['description'], url=url,
                     image_key=image_key, tags=tags.fetchall())


class RawImageHandler(Handler):
    def get(self, image_key):
        image = self.db.execute('SELECT * FROM images WHERE key = ?',
                                (image_key,)).fetchone()
        if image is None:
            self.set_status(404)
            return

        if image['file'] is None:
            self.redirect(image['url'])

        self.redirect('/static/' + image['file'])


class NewImageHandler(Handler):
    def get(self):
        self.render('images/new.html')

    def post(self):
        name = self.get_body_argument("name")
        url = self.get_body_argument("url")
        description = self.get_body_argument("description")
        image = url.split('/')[-1]
        key = image.split('.')[0]

        with self.db:
            self.db.execute(
                'INSERT INTO images (name, key, url, description) '
                'VALUES (?, ?, ?, ?)', (name, key, url, description))

        self.redirect('/images/{}'.format(key))


def get_tags_json(db, image_key):
    image_id = db.execute('SELECT id FROM images WHERE key = ?',
                          [image_key]).fetchone()
    if image_id is None:
        return None

    image_id = image_id[0]
    tags = db.execute('SELECT tags.name FROM image_tags '
                      'INNER JOIN tags ON tags.id = tag_id '
                      'WHERE image_id = ?', [image_id])
    output = json.dumps([tag['name'] for tag in tags.fetchall()])
    return output


class ImageTagsHandler(Handler):
    def get(self, image_key):
        output = get_tags_json(self.db, image_key)
        if output is None:
            self.set_status(404)
            return

        self.set_header("Content-Type", "text/json")
        self.write(output)


class ImageAddTagHandler(Handler):
    def post(self, image_key):
        image_id = self.db.execute('SELECT id FROM images WHERE key = ?',
                                   (image_key,)).fetchone()
        if image_id is None:
            self.set_status(404)
            return
        image_id = image_id['id']

        tag_name = self.get_body_argument('name')
        tag_id = self.db.execute('SELECT id FROM tags WHERE name = ?',
                                 (tag_name,)).fetchone()
        if tag_id is None:
            with self.db:
                self.db.execute('INSERT INTO tags (name) VALUES (?)',
                                (tag_name,))
            tag_id = self.db.execute('SELECT id FROM tags WHERE name = ?',
                                     (tag_name,)).fetchone()
        tag_id = tag_id['id']

        with self.db:
            self.db.execute('INSERT INTO image_tags (tag_id, image_id) '
                            'VALUES (?, ?)', (tag_id, image_id))

        self.set_header("Content-Type", "text/json")
        self.write(get_tags_json(self.db, image_key))


class ListTagHandler(Handler):
    def get(self):
        tags = self.db.execute('SELECT name FROM tags').fetchmany(100)
        self.render('tags/index.html', tags=tags)


class ViewTagHandler(Handler):
    def get(self, tag_name):
        tag_name = tag_name.replace('+', ' ')
        tag = self.db.execute('SELECT * FROM tags WHERE name = ?',
                              [tag_name]).fetchone()

        if tag is None:
            self.set_status(404)
            return

        images = self.db.execute(
            'SELECT images.key, images.name FROM image_tags '
            'INNER JOIN images ON images.id = image_id '
            'WHERE tag_id = ?', [tag['id']]).fetchmany(100)
        self.render('tags/show.html', name=tag_name, images=images)


class StaticFileHandler(tornado.web.RequestHandler):
    def get(self, path):
        content_type = 'text/plain'
        if path[-4:] == '.jpg':
            content_type = 'image/jpeg'
        elif path[-4:] == '.png':
            content_type = 'image/png'
        elif path[-4:] == '.gif':
            content_type = 'image/gif'

        self.set_header('Content-Type', content_type)
        text = open(path, 'r').read()
        self.write(text)


class NewTagHandler(Handler):
    def get(self):
        self.render('tags/new.html')

    def post(self):
        name = self.get_body_argument("name")
        with db:
            self.db.execute('INSERT INTO tags (name) VALUES (?)',
                            (name,))
        name = name.replace(' ', '+')
        self.redirect('/tags/{}'.format(name))


def make_app(db):
    db = {'db': db}
    return tornado.web.Application([
        (r'/', ListImageHandler, db),
        (r'/static/(.*)', StaticFileHandler),
        (r'/images/?', ListImageHandler, db),
        (r'/images.json', ListImageJSON, db),
        (r'/images/new/?', NewImageHandler, db),
        (r'/images/([^/]+)/?', ShowImageHandler, db),
        (r'/images/([^/]+)/raw', RawImageHandler, db),
        (r'/images/([^/]+)/tags.json', ImageTagsHandler, db),
        (r'/images/([^/]+)/tags/new/?', ImageAddTagHandler, db),
        (r'/tags/?', ListTagHandler, db),
        (r'/tags/new/?', NewTagHandler, db),
        (r'/tags/([^/]+)/?', ViewTagHandler, db),
    ], debug=True, template_path='web/')


if __name__ == '__main__':
    db = database.make_db('imp.db')
    app = make_app(db)
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
