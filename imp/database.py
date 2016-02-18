import migrations


class Tag(object):
    def __init__(self, row):
        self.id = row['id']
        self.name = row['name']
        self.category_id = row['category_id']

class Category(object):
    def __init__(self, row):
        self.id = row['id']
        self.name = row['name']

class Image(object):
    def __init__(self, row):
        self.id = row['id']
        self.key = row['key']
        self.name = row['name']
        self.url = row['url']
        self.file = row['file']
        self.description = row['description']

class Database(object):
    def __init__(self, name):
        self.db = migrations.migrate_db(name)

    def execute(self, text, *items):
        return self.db.execute(text, *items)

    def __enter__(self, *args):
        self.db.__enter__(*args)

    def __exit__(self, *args):
        self.db.__exit__(*args)

    def categories(self):
        return [Category(row) for row in
                self.execute('SELECT id, name FROM categories;'
                         ).fetchall()]

    def tags(self):
        return [Tag(row) for row in
                self.execute('SELECT id, name, category_id FROM tags;'
                         ).fetchall()]

    def images(self):
        return [Image(row) for row in
                self.execute('SELECT id, key, name, url, file, description '
                             'FROM images;'
                         ).fetchall()]
