import sqlite3
import json
import tornado.ioloop
import tornado.web
import database
import random
import argparse
import os


class HttpError(Exception):
    def __init__(self, code, msg):
        super(Exception, self).__init__(msg)
        self.code = code


def tag_category(tag, db):
    cat = db.execute('SELECT name FROM categories WHERE id = ?',
                     (tag['category_id'],)).fetchone()
    if cat is None:
        return None
    return cat['name'].title()


def add_image_tag(db, name, category):
    print("NAME: {}, CATEGORY: {}".format(name, category))
    if category:
        category_id = get_category_id(db, category)
    else:
        category_id = None

    with db:
        db.execute('INSERT INTO tags (name, category_id) '
                   'VALUES (?, ?)', (name, category_id))

def get_category_id(db, name):
    category_id = db.execute(
        'SELECT id FROM categories WHERE name = ?',
        (name,)).fetchone()
    if category_id is None:
        with db:
            db.execute('INSERT INTO categories (name) VALUES (?)',
                        (name.title(),))
        category_id = db.execute(
            'SELECT id FROM categories WHERE name = ?',
            (name,)).fetchone()
    return category_id['id']

class Handler(tornado.web.RequestHandler):
    def initialize(self, db):
        self.db = db

    def get(self, *args, **kwargs):
        if self.request.uri[-5:] == '.json':
            self.set_header('Content-Type', 'application/json')
            try:
                assert self.api_get(*args, **kwargs) is None
            except HttpError as e:
                self.set_status(e.code)
        else:
            try:
                assert self.page_get(*args, **kwargs) is None
            except HttpError as e:
                self.set_status(e.code)


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
        img = self.db.execute('SELECT * FROM images WHERE key = ?',
                              [image_key]).fetchone()
        if img is None:
            raise HttpError(404, "Image '{}' not found".format(image_key))
        return img

    def get_image_tags(self, image):
        return self.db.execute('SELECT tags.name FROM image_tags '
                               'INNER JOIN tags ON tags.id = tag_id '
                               'WHERE image_id = ?',
                               [image['id']]).fetchall()

    def get_image_url(self, image):
        if image['file'] is None:
            return image['url']
        return '/static/' + image['file']


    def page_get(self, image_key):
        image = self.get_image(image_key)
        tags = self.get_image_tags(image)
        url = self.get_image_url(image)

        self.render('images/show.html', name=image['name'],
                    desc=image['description'], url=url,
                    image_key=image_key, tags=tags)

    def api_get(self, image_key):
        image = self.get_image(image_key)
        tags = self.get_image_url(image)
        url = self.get_image_url(image)

        self.write(json.dumps({
            'name': image['name'],
            'description': image['description'],
            'key': image['key'],
            'url': url,
            'tags': [tag.title() for tag in tags],
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


def get_tags_json(db, image_key):
    image_id = db.execute('SELECT id FROM images WHERE key = ?',
                          [image_key]).fetchone()
    if image_id is None:
        return None

    image_id = image_id[0]
    tags = db.execute('SELECT tags.name FROM image_tags '
                      'INNER JOIN tags ON tags.id = tag_id '
                      'WHERE image_id = ?', [image_id])
    output = json.dumps([tag['name'].title() for tag in tags.fetchall()])
    return output


class RandomImageHandler(Handler):
    def random_image_key(self):
        # TODO (2016-02-16) Caleb Jones:
        # Performance (can we get randomness in the database?)
        images = self.db.execute('SELECT key FROM images;').fetchall()
        if not images:
            raise HttpError(404, "No images, cannot select random image")
        return random.choice(images)['key']

    def get_page(self):
        try:
            key = self.random_image_key()
        except HttpError:
            self.redirect('/')
        self.redirect('/images/{}'.format(key))

    def get_api(self):
        key = self.random_image_key()
        url = '/images/{}'.format(key)
        self.write(json.dumps({'key': key, 'url': url}))


class ImageTagsHandler(Handler):
    def get(self, image_key):
        self.set_header('Content-Type', 'application/json')
        output = get_tags_json(self.db, image_key)
        if output is None:
            self.set_status(404)
            return

        self.write(output)


class ImageAddTagHandler(Handler):
    def post(self, image_key):
        image_id = self.db.execute('SELECT id FROM images WHERE key = ?',
                                   (image_key,)).fetchone()
        if image_id is None:
            self.set_status(404)
            return
        image_id = image_id['id']

        tag_name = self.get_body_argument('name').title().strip()
        tag_category = self.get_body_argument('category', '').title().strip()
        tag_id = self.db.execute('SELECT id FROM tags WHERE name = ?',
                                 (tag_name,)).fetchone()
        if tag_id is None:
            add_image_tag(self.db, tag_name, tag_category)
            tag_id = self.db.execute('SELECT id FROM tags WHERE name = ?',
                                     (tag_name,)).fetchone()
        tag_id = tag_id['id']

        with self.db:
            self.db.execute('INSERT INTO image_tags (tag_id, image_id) '
                            'VALUES (?, ?)', (tag_id, image_id))

        self.set_header("Content-Type", "text/json")
        self.write(get_tags_json(self.db, image_key))


class ListTagHandler(Handler):
    def get_tags(self):
        tags = self.db.execute('SELECT tags.name, categories.name '
                               'FROM tags '
                               'LEFT JOIN categories '
                               'ON categories.id = category_id '
                               'ORDER BY categories.name').fetchall()
        return [{'name': name.title(),
                 'category': cat.title() if cat else None}
                for name, cat in tags]

    def page_get(self):
        self.render('tags/index.html', tags=self.get_tags())

    def api_get(self):
        self.write(json.dumps(self.get_tags()))


class ViewTagHandler(Handler):
    def get(self, tag_name):
        tag_name = tag_name.replace('+', ' ').title()
        tag = self.db.execute('SELECT * FROM tags WHERE name = ?',
                              (tag_name,)).fetchone()

        if tag is None:
            self.set_status(404)
            return

        category = self.db.execute(
            'SELECT * FROM categories WHERE id = ?',
            (tag['category_id'],)).fetchone()
        if category is not None:
            category = category['name']

        images = self.db.execute(
            'SELECT images.key, images.name FROM image_tags '
            'INNER JOIN images ON images.id = image_id '
            'WHERE tag_id = ?', [tag['id']]).fetchmany(100)
        self.render('tags/show.html', name=tag_name,
                    images=images, category=category)


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
        content = open(path, 'rb').read()
        self.write(content)


class NewTagHandler(Handler):
    def get(self):
        self.render('tags/new.html')

    def post(self):
        name = self.get_body_argument('name').title().strip()
        category = self.get_body_argument('category', '').title().strip()
        add_image_tag(self.db, name, category)
        name = name.replace(' ', '+')
        self.redirect('/tags/{}'.format(name))


class ListCategoryHandler(Handler):
    def get_categories(self):
        categories = self.db.execute('SELECT * FROM categories;').fetchall()
        return [{'name': cat['name'].title()} for cat in categories]

    def api_get(self):
        self.write(json.dumps(self.get_categories()))

    def page_get(self):
        self.render('categories/index.html', categories=self.get_categories())


class NewCategoryHandler(Handler):
    def get(self):
        self.render('categories/new.html')

    def post(self):
        name = self.get_body_argument('name')
        with self.db:
            self.db.execute('INSERT INTO categories (name) VALUES (?)',
                            (name,))
        name = name.replace(' ', '+')
        # TODO (2016-02-16) Caleb Jones:
        # Don't redirect AJAX calls, only the client
        self.redirect('/categories/{}'.format(name))

class ShowCategoryHandler(Handler):
    def get_category_data(self, name):
        name = name.replace('+', ' ')
        category = self.db.execute('SELECT * FROM categories WHERE name = ?',
                                   (name,)).fetchone()
        if category is None:
            raise HttpError(404, "Category '{}' not found".format(name))

        tags = self.db.execute('SELECT * FROM tags WHERE category_id = ?',
                               (category['id'],)).fetchall()
        tags = [tag['name'].title() for tag in tags]
        return {'name': category['name'].title(), 'tags': tags}

    def api_get(self, category_name):
        data = self.get_category_data(category_name)
        self.write(json.dumps(data))

    def page_get(self, category_name):
        data = self.get_category_data(category_name)
        self.render('categories/show.html', **data)


class CategoryTagsHandler(Handler):
    def get_tags_for_category(self, name):
        category = self.db.execute('SELECT id FROM categories WHERE name = ?',
                                   (name,)).fetchone()
        if category is None:
            raise HttpError(404, "Category '{}' not found".format(name))
        return self.db.execute('SELECT name FROM tags WHERE category_id = ?',
                               (category['id'],)).fetchall()

    def api_get(self, category_name):
        category_name = category_name.replace('+', ' ').title()
        tags = self.get_tags_for_category(category_name)
        tags = [tag['name'].title() for tag in tags]
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
        (r'/categories/?', ListCategoryHandler, db),
        (r'/categories/new/?', NewCategoryHandler, db),
        (r'/categories/([^/]+)\.json', ShowCategoryHandler, db),
        (r'/categories/([^/]+)/?', ShowCategoryHandler, db),
        (r'/categories/([^/]+)/tags\.json', CategoryTagsHandler, db),
    ], debug=True, template_path='web/')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Serve a webpage that presents imp's data")
    parser.add_argument('-p', '--port', type=int, default=8888,
                        help="the port to run the server on")
    parser.add_argument('-d', '--database', metavar='DB', default='imp.db',
                        type=str, help="the name of the database to use")

    args = parser.parse_args()
    directory = os.path.dirname(args.database)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    db = database.make_db(args.database)
    app = make_app(db)
    app.listen(args.port)
    print("Listening at http://localhost:{}/".format(args.port))
    tornado.ioloop.IOLoop.current().start()
