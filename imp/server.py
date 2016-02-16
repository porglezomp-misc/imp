import sqlite3
import json
import tornado.ioloop
import tornado.web
import database
import random


def tag_category(tag, db):
    cat = db.execute('SELECT name FROM categories WHERE id = ?',
                     (tag['category_id'],)).fetchone()
    if cat is None:
        return None
    return cat['name']


class Handler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    def get(self, *args, **kwargs):
        if self.request.uri[-5:] == '.json':
            self.set_header('Content-Type', 'application/json')
            assert self.api_get(*args, **kwargs) is None
        else:
            assert self.page_get(*args, **kwargs) is None


class ListImageHandler(Handler):
    def page_get(self):
        images = self.db.execute("SELECT key, name FROM images;")
        self.render('images/index.html', images=images.fetchall())

    def api_get(self):
        images = self.db.execute("SELECT * FROM images")
        entries = [{'key': img['key'], 'name': img['name']}
                   for img in images.fetchall()]
        out = json.dumps(entries)
        self.write(out)


class ShowImageHandler(Handler):
    def get_image(self, image_key):
        return self.db.execute('SELECT * FROM images WHERE key = ?',
                               [image_key]).fetchone()

    def get_image_tags(self, image):
        return self.db.execute('SELECT tags.name FROM image_tags '
                               'INNER JOIN tags ON tags.id = tag_id '
                               'WHERE image_id = ?', [image['id']])

    def get_image_url(self, image):
        if image['file'] is None:
            url = image['url']
        else:
            url = '/static/' + image['file']
        return url


    def page_get(self, image_key):
        image = self.get_image(image_key)
        if image is None:
            self.set_status(404)
            self.write('image not found')
            return

        tags = self.get_image_tags(image)
        url = self.get_image_url(image)

        self.render('images/show.html', name=image['name'],
                    desc=image['description'], url=url,
                    image_key=image_key, tags=tags.fetchall())

    def api_get(self, image_key):
        image = self.get_image(image_key)
        if image is None:
            self.set_status(404)
            return

        tags = self.get_image_url(image)
        url = self.get_image_url(image)

        self.write(json.dumps({
            'name': image['name'],
            'description': image['description'],
            'key': image['key'],
            'url': url,
            'tags': tags,
        }))


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


class RandomImageHandler(Handler):
    def random_image_key(self):
        # TODO (2016-02-16) Caleb Jones:
        # Performance (can we get randomness in the database?)
        images = self.db.execute('SELECT key FROM images;').fetchall()
        if not images:
            return None
        return random.choice(images)['key']

    def get_page(self):
        key = self.random_image_key()
        if key is None:
            self.redirect('/')
        self.redirect('/images/{}'.format(key))

    def get_api(self):
        key = self.random_image_key()
        if key is None:
            self.set_status(404)
            return
        url = '/images/{}'.format(key)
        self.write(json.dumps({'key': key, 'url': url}))


class ImageTagsHandler(Handler):
    def get(self, image_key):
        self.set_header('Content-Type', 'application/json')
        image_id = self.db.execute('SELECT id FROM images WHERE key = ?',
                                   [image_key]).fetchone()
        if image_id is None:
            self.set_status(404)
            return

        image_id = image_id[0]
        tags = self.db.execute('SELECT tags.name, tags.category_id FROM image_tags '
                               'INNER JOIN tags ON tags.id = tag_id '
                               'WHERE image_id = ?', [image_id])
        tags = [{'name': tag['name'], 'category': tag_category(tag, self.db)}
                for tag in tags.fetchall()]
        output = json.dumps(tags)
        self.write(output)


class ImageAddTagHandler(Handler):
    def get(self, image_key):
        self.render('images/add_tag.html', image_key=image_key)

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
        self.redirect('/images/{}'.format(image_key))


class ListTagHandler(Handler):
    def page_get(self):
        tags = self.db.execute('SELECT name FROM tags').fetchall()
        self.render('tags/index.html', tags=tags)

    def api_get(self):
        tags = self.db.execute('SELECT * FROM tags').fetchall()

        tags = [{'name': tag['name'], 'category': tag_category(tag, self.db)}
                for tag in tags]
        self.write(json.dumps(tags))


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
    def get_category_id(self, name):
        category_id = self.db.execute(
            'SELECT id FROM categories WHERE name = ?',
            (name,)).fetchone()
        if category_id is None:
            with db:
                self.db.execute('INSERT INTO categories (name) VALUES (?)',
                                (name,))
            category_id = self.db.execute(
                'SELECT id FROM categories WHERE name = ?',
                (name,)).fetchone()
        return category_id['id']

    def get(self):
        self.render('tags/new.html')

    def post(self):
        name = self.get_body_argument('name')
        category = self.get_body_argument('category')
        if category:
            category_id = self.get_category_id(category)
        else:
            category_id = None

        with db:
            self.db.execute('INSERT INTO tags (name, category_id) '
                            'VALUES (?, ?)', (name, category_id))
        name = name.replace(' ', '+')
        self.redirect('/tags/{}'.format(name))


class ListCategoryHandler(Handler):
    def get_categories(self):
        return self.db.execute('SELECT * FROM categories;').fetchall()

    def api_get(self):
        categories = self.get_categories()
        items = [{'name': cat['name']} for cat in categories]
        self.write(json.dumps(items))


class ShowCategoryHandler(Handler):
    def api_get(self, category_name):
        category = self.db.execute('SELECT * FROM categories WHERE name = ?',
                                   (category_name,)).fetchone()
        if category is None:
            self.set_status(404)
            return

        tags = self.db.execute('SELECT * FROM tags WHERE category_id = ?',
                               (category['id'],)).fetchall()
        tags = [tag['name'] for tag in tags]
        self.write(json.dumps({
            'name': category['name'],
            'tags': tags,
        }))
        

class CategoryTagsHandler(Handler):
    def get_tags_for_category(self, name):
        category = self.db.execute('SELECT id FROM categories WHERE name = ?',
                                   (name,)).fetchone()
        if category is None:
            return None
        return self.db.execute('SELECT name FROM tags WHERE category_id = ?',
                               (category['id'],)).fetchall()

    def api_get(self, category_name):
        category_name = category_name.replace('+', ' ')
        tags = self.get_tags_for_category(category_name)
        if tags is None:
            self.set_status(404)
            return
        tags = [tag['name'] for tag in tags]
        self.write(json.dumps(tags))


def make_app(db):
    db = {'db': db}
    return tornado.web.Application([
        (r'/', ListImageHandler, db),
        (r'/static/(.*)', StaticFileHandler),

        (r'/images\.json', ListImageHandler, db),
        (r'/images/?', ListImageHandler, db),
        (r'/images/new/?', NewImageHandler, db),
        (r'/images/random\.json', RandomImageHandler, db),
        (r'/images/random/?', RandomImageHandler, db),
        (r'/images/([^/]+)\.json', ShowImageHandler, db),
        (r'/images/([^/]+)/?', ShowImageHandler, db),
        (r'/images/([^/]+)/raw', RawImageHandler, db),
        (r'/images/([^/]+)/tags\.json', ImageTagsHandler, db),
        (r'/images/([^/]+)/tags/new/?', ImageAddTagHandler, db),

        (r'/tags\.json', ListTagHandler, db),
        (r'/tags/?', ListTagHandler, db),
        (r'/tags/new/?', NewTagHandler, db),
        (r'/tags/([^/]+)/?', ViewTagHandler, db),

        (r'/categories\.json', ListCategoryHandler, db),
        (r'/categories/([^/]+)\.json', ShowCategoryHandler, db),
        (r'/categories/([^/]+)/tags\.json', CategoryTagsHandler, db),
    ], debug=True, template_path='web/')


if __name__ == '__main__':
    db = database.make_db('imp.db')
    app = make_app(db)
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
