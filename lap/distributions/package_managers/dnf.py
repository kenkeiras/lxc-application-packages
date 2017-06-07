import re
import os
import requests

from xml.dom.minidom import (
    parseString,
    parse as parseFile,
    Text as TextNode,
)

from ...conventions import LOCAL_PATH
from .. import readers

class DNFRepositoryMetalink:
    def __init__(self, baseurl, repo, architecture):
        self.baseurl = baseurl
        self.repo = repo
        self.architecture = architecture
        self.url = '{base}?repo={repo}&arch={arch}'.format(
            base=baseurl, repo=repo, arch=architecture)
        self.identifier = re.sub(r'[^a-zA-Z0-9_]', '_',
            '{}/{}/{}'
            .format(baseurl, repo, architecture)
        )

    def get_repositories(self):
        req = requests.get(self.url)
        tree = parseString(req.text)
        urls = tree.getElementsByTagName('url')
        https_urls = [url for url in urls if url.getAttribute('protocol') == 'https']
        for https_url in sorted(https_urls, key=lambda x: int(x.getAttribute("preference"))):
            url = https_url.childNodes[0].wholeText
            print('Downloading data from {url}'.format(url=url))
            yield DNFRepository(url)

    def download_to(self, dir_name):
        cache_file_name = self.identifier
        if os.path.exists(os.path.join(dir_name, 'data.xml.gz')):
            return

        for repository in self.get_repositories():
            try:
                return repository.download_to(dir_name)
            except Exception as e:
                print(e)

class DNFRepository:
    def __init__(self, url):
        self.url = url

    def download_to(self, dir_name):
        os.makedirs(dir_name, exist_ok=True)

        data = parseString(requests.get(self.url).text)
        primary = [node
                   for node
                   in data.getElementsByTagName('data')
                   if node.getAttribute('type') == 'primary'][0]

        tree_base = re.sub(r'/tree/.*', '/tree/', self.url)
        extension = primary.getElementsByTagName('location')[0].getAttribute('href')

        url = tree_base + extension

        with open(os.path.join(dir_name, 'data.xml.gz'), 'wb') as f:
            r = requests.get(url)
            f.write(readers.gz(r.content))


def getText(node):
    return node.childNodes[0].wholeText


def parse_package(package):
    nodes = { node.tagName: node
              for node
              in package.childNodes
              if not isinstance(node, TextNode)
    }

    data = {
        'Package': getText(nodes['name']),
        'Description': getText(nodes['summary']),
        'Section': (getText(nodes['format']
                            .getElementsByTagName('rpm:group')[0])),
    }

    if len(nodes['format'].getElementsByTagName('rpm:requires')) != 0:
        nodes['Dependencies'] = [
            entry.getAttribute('name')
            for entry in (nodes['format']
                          .getElementsByTagName('rpm:requires')[0]
                          .getElementsByTagName('rpm:entry'))
        ]


    yield data


class DNFCacheReader:
    def __init__(self, repositories, identifier):
        cache_dir = get_cache_path(identifier)
        self.paths = []
        for repo in repositories:
            self.paths.append(os.path.join(cache_dir, repo.identifier, 'data.xml.gz'))
            assert(os.path.exists(self.paths[-1]))

    def get_packages(self):
        for fname in self.paths:
            with open(fname, 'rt') as f:
                tree = parseFile(f)
                for package in tree.getElementsByTagName('package'):
                    yield from parse_package(package)

def get_cache_path(identifier):
    return os.path.join(LOCAL_PATH, 'cache', identifier + '.cache')


def build_cache(repositories, identifier):
    cache_dir = get_cache_path(identifier)
    os.makedirs(cache_dir, exist_ok=True)
    for repo in repositories:
        repo.download_to(os.path.join(cache_dir, repo.identifier))

