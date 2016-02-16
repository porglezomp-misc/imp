import migrations


def Database(name):
    return migrations.migrate_db(name)
