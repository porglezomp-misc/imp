from __future__ import print_function

import requests
import sys
import logging
import os
import sys
import json
import click
from imgurpython import ImgurClient

import database


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger('requests').setLevel(logging.WARN)
logging.getLogger('urllib3').setLevel(logging.WARN)
db = None


def download_image(url, location):
    url = url.replace('http:', 'https:')
    logger.info("Downloading %s to %s", url, location)
    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        logger.error("Error %d while downloding %s", r.status_code, url)
        return
    with open(location, 'wb') as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)
    logger.info("Finished downloading %s to %s", url, location)


def record_image(db, url, title, description, source=None):
    fname = url.split('/')[-1]
    key = fname.split('.')[0]
    i = db.execute('SELECT id FROM images WHERE key = ?', [key])
    if i.fetchone() is None:
        with db:
            logger.info("INSERT INTO images (name, key, url, description) "
                        "VALUES ('%s', '%s', '%s', '%s');",
                        title, key, url, description or 'NULL')
            db.execute('INSERT INTO images (name, key, url, description) '
                       'VALUES (?, ?, ?, ?);',
                       (title, key, url, description))


RESOURCES = 'resources'


def download_from_database(db):
    not_downloaded = db.execute('SELECT * FROM images WHERE file IS NULL;')
    if not os.path.isdir(RESOURCES):
        os.mkdir(RESOURCES)
    for image in not_downloaded.fetchall():
        fname = image['url'].split('/')[-1]
        fname = os.path.join(RESOURCES, fname)
        download_image(image['url'], fname)
        with db:
            db.execute('UPDATE images SET file = ? WHERE id = ?',
                       (fname, image['id']))
            logger.info("UPDATE images SET file = '%s' WHERE id = %s",
                       fname, image['id'])


def locate_images(db, client, subreddit):
    from imgurpython.helpers.error import ImgurClientRateLimitError
    try:
        vals = client.subreddit_gallery(subreddit)
    except ImgurClientRateLimitError as e:
        print(e.error_message)
        print(e.status_code)
        return False
    else:
        for val in vals:
            val.link = val.link.replace('http:', 'https:')
            record_image(db, val.link, val.title, val.description)
    return True


def get_client():
    with open('SECRET', 'r') as f:
        vals = json.loads(f.read())
        client_id = vals['client_id']
        client_secret = vals['client_secret']
    return ImgurClient(client_id, client_secret)


@click.group()
def main():
    pass


@main.command(help='download from a single subreddit')
@click.argument('reddit')
def sub(reddit):
    db = database.make_db('imp.db')
    client = get_client()
    locate_images(db, client, reddit)
    download_from_database(db)


@main.command(help='download multiple subreddits based on a manifest file')
@click.argument('file')
def multi(file):
    pass


if __name__ == '__main__':
    main()
