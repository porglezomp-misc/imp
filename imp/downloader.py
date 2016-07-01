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
    images = not_downloaded.fetchall()
    if images:
        print("Downloading images: {:03}/{:03}".format(0, len(images)), end='')
        sys.stdout.flush()
    for i, image in enumerate(images):
        fname = image['url'].split('/')[-1]
        fname = os.path.join(RESOURCES, fname)
        download_image(image['url'], fname)
        with db:
            db.execute('UPDATE images SET file = ? WHERE id = ?',
                       (fname, image['id']))
            logger.info("UPDATE images SET file = '%s' WHERE id = %s",
                       fname, image['id'])
        print("\rDownloading images: {:03}/{:03}".format(i+1, len(images)), end='')
        sys.stdout.flush()
    print()


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
@click.option('-v', '--verbose', count=True, default=0)
def main(verbose):
    if verbose == 0:
        logging.getLogger(__name__).setLevel(logging.WARN)
    if verbose == 1:
        logging.getLogger(__name__).setLevel(logging.INFO)
    if verbose >= 2:
        logging.getLogger(__name__).setLevel(logging.DEBUG)
        if verbose >= 3:
            logging.getLogger('requests').setLevel(logging.INFO)
            logging.getLogger('urllib3').setLevel(logging.INFO)


@main.command(help='download from a single subreddit')
@click.argument('reddit')
def sub(reddit):
    db = database.make_db('imp.db')
    client = get_client()
    locate_images(db, client, reddit)
    download_from_database(db)


@main.command(help='download multiple subreddits based on a manifest file')
@click.argument('filename')
def multi(filename):
    db = database.make_db('imp.db')
    with open(filename, 'r') as f:
        items = []
        for num, line in enumerate(f):
            line = line.strip()
            if line[0] == '#' or line == '':
                continue
            elif line[0] == '*':
                line = line.lstrip('*')
                line = line.split('#')[0]
                line = line.strip()
                line = line.split('/')[-1]
                items.append(line)
            else:
                print("Error, line {}:".format(num+1))
                print("Expected '*' or '#' at the beginning of the line, skipping...")
                print(line)
        if items:
            client = get_client()
            for location in items:
                print("Downloading from {}".format(location))
                locate_images(db, client, location)
    download_from_database(db)


@main.command(help='finish downloading cached images')
def flush():
    db = database.make_db('imp.db')
    download_from_database(db)


if __name__ == '__main__':
    main()
