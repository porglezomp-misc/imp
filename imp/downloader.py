from __future__ import print_function

import requests
import bs4
import sys
import logging
import os
import sys
import sqlite3

import database


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
db = None


def download_image(url, location):
    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        logger.error("Error %d while downloding %s", r.status_code, url)
        return
    with open(location, 'wb') as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)
    logger.info("Finished downloading %s to %s", url, location)


def record_image(url, title):
    f = url.split('/')[-1]
    key = f.split('.')[0]
    i = db.execute('SELECT id FROM images WHERE key = ?', [key])
    if i.fetchone() is None:
        with db:
            logger.info("INSERT INTO images (name, key, url) "
                        "VALUES ('%s', '%s', '%s');", title, key, url)
            db.execute('INSERT INTO images (name, key, url) '
                       'VALUES (?, ?, ?);', (title, key, url))


def locate_image(url, save_into=''):
    r = requests.get(url)
    html = bs4.BeautifulSoup(r.text, 'html.parser')
    imgs = html.select('.post-image a img')
    for img in imgs:
        url = 'https:' + img['src'].rstrip('?0123456789')
        logger.info("Downloading %s", url)
        title = html.select('h1.post-title')[0].text
        record_image(url, title)


def find_many(source, dest):
    if not os.path.isdir(dest):
        os.mkdir(dest)

    r = requests.get(source)
    html = bs4.BeautifulSoup(r.text, 'html.parser')
    links = html.find_all('a', class_='image-list-link')
    keys = {row[0] for row in db.execute('SELECT key FROM images;').fetchall()}

    for link in links:
        urlkey = link['href'].split('/')[-1].split('.')[0]
        if urlkey in keys:
            logger.info('%s already downloaded, skipping', link['href'])
        else:
            url = 'https://imgur.com' + link['href']
            # TODO: Concurrent processing
            locate_image(url, save_into=dest)


RESOURCES = 'resources'

if __name__ == '__main__':
    # TODO: Command line interface
    db = database.make_db('imp.db')
    find_many(sys.argv[1], 'out')
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
