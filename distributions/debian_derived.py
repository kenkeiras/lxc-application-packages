# coding: utf-8

from . import readers

import re
import os.path
import hashlib
import requests

class DebianRepository:
    def __init__(self, uri, suite, components, architecture='amd64'):
        self.uri = uri
        self.suite = suite
        self.components = components
        self.architecture = architecture
        self.identifier = re.sub(r'[^a-zA-Z0-9_]', '_',
            '{}/{}/{}/{}'
            .format(uri, suite, components, architecture)
        )

    def download_to(self, dir_name):
        for component in self.components:
            os.makedirs(dir_name, exist_ok=True)
            cache_file_name = os.path.join(dir_name, component)
            if os.path.exists(cache_file_name):
                continue

            base_url = ('{}/dists/{}/{}/binary-{}/Packages'
                        .format(self.uri,
                                self.suite,
                                component,
                                self.architecture))
            for (extension, reader) in (('.xz', readers.xz), ('.bz2', readers.bz),
                                        ('.gz', readers.gz), ('', readers.plain)):
                with open(cache_file_name, 'wb') as f:
                    r = requests.get(base_url + extension)
                    f.write(reader(r.content))
                break



class DebianCacheReader:
    def __init__(self, repositories, identifier):
        cache_dir = get_cache_path(identifier)
        self.paths = []
        for repo in repositories:
            repo_dir = os.path.join(cache_dir, repo.identifier)
            for component in repo.components:
                self.paths.append(os.path.join(repo_dir, component))
                assert(os.path.exists(self.paths[-1]))

    def get_packages(self):
        for fname in self.paths:
            with open(fname, 'rt') as f:
                data = {}
                last_key = None
                for l in f:
                    l = l.rstrip()
                    if len(l) == 0:
                        yield data
                        data = {}
                        last_key = None

                    elif l.startswith(' '):
                        data[last_key] += l

                    else:
                        key, value = l.split(': ', 1)
                        data[key] = value
                        last_key = key


def get_cache_path(identifier):
    return 'cache/' + identifier + '.cache'


def build_cache(repositories, identifier):
    cache_dir = get_cache_path(identifier)
    os.makedirs(cache_dir, exist_ok=True)
    for repo in repositories:
        repo.download_to(os.path.join(cache_dir, repo.identifier))


class DebianDerived:
    def __init__(self, repositories, identifier):
        self.repositories = repositories
        self.identifier = identifier

    def get_packages(self):
        build_cache(self.repositories, self.identifier)
        reader = DebianCacheReader(self.repositories, self.identifier)
        yield from reader.get_packages()
