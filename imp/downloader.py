import requests
import bs4
import sys
import logging
import os
import sys

logger = logging.getLogger(__name__)


def download_image(url, location):
    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        logger.error("Error %d while downloding %s", r.status_code, url)
        return
    with open(location, 'wb') as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)
    logger.info("Finished downloading %s to %s", url, location)


def locate_image(url, save_into=''):
    r = requests.get(url)
    html = bs4.BeautifulSoup(r.text, 'html.parser')
    imgs = html.select('.post-image a img')
    for img in imgs:
        url = 'https:' + img['src'].rstrip('?0123456789')
        logger.info("Downloading %s", url)
        title = url.lstrip('https://i.imgur.com/')
        location = os.path.join(save_into, title)
        download_image(url, location)


def download_many(source, dest):
    if not os.path.isdir(dest):
        os.mkdir(dest)

    r = requests.get(source)
    html = bs4.BeautifulSoup(r.text, 'html.parser')
    links = html.find_all('a', class_='image-list-link')

    for link in links:
        url = 'https://imgur.com' + link['href']
        # TODO: Concurrent processing
        locate_image(url, save_into=dest)


if __name__ == '__main__':
    # TODO: Command line interface
    download_many(sys.argv[1], 'out')
