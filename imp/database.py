import migrations


class Database(object):
    def __init__(self, name):
        self.db = migrations.migrate_db(name)

    def execute(self, text, *items):
        return self.db.execute(text, *items)

    def __enter__(self, *args):
        self.db.__enter__(*args)

    def __exit__(self, *args):
        self.db.__exit__(*args)
