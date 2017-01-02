# coding: utf-8

import lxc

from . import readers

import getpass
import re
import os.path
import hashlib
import requests

from os.path import expanduser
LOCAL_PATH = os.path.join(expanduser("~"), '.local', 'share', 'lap')

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
    return os.path.join(LOCAL_PATH, 'cache', identifier + '.cache')


def build_cache(repositories, identifier):
    cache_dir = get_cache_path(identifier)
    os.makedirs(cache_dir, exist_ok=True)
    for repo in repositories:
        repo.download_to(os.path.join(cache_dir, repo.identifier))


class DebianDerived:
    GRAPHICAL_APP_REQUIREMENTS = ['x11-common', 'libx11-data', 'libdrm2']

    def __init__(self, repositories, identifier):
        self.repositories = repositories
        self.identifier = identifier

    def get_packages(self):
        build_cache(self.repositories, self.identifier)
        reader = DebianCacheReader(self.repositories, self.identifier)
        yield from reader.get_packages()


    def package_map(self):
        pkg_map = {}
        for pkg in self.get_packages():
            pkg_map[pkg['Package']] = pkg
        return pkg_map


    def has_application(self, application):
        return len([True for pkg in self.get_packages() if pkg['Package'] == application]) > 0


    def is_graphical(self, application):
        pkg_map = self.package_map()
        dependencies = [application]
        checked = set()
        while len(dependencies) > 0:
            dep = pkg_map[dependencies.pop()]
            if 'Depends' not in dep:
                continue

            subdeps = [subdep.split(' ', 1)[0] for subdep in dep['Depends'].split(', ')]
            for subdep in subdeps:
                if subdep in self.GRAPHICAL_APP_REQUIREMENTS:
                    return True

                if not subdep in checked:
                    checked.add(subdep)
                    dependencies.append(subdep)

        return False


    def configure_first_time(self, container, configuration):
        # Create the user
        username = getpass.getuser()
        container.attach_wait(lxc.attach_run_command, ['useradd', username])
        container.attach_wait(lxc.attach_run_command, ['mkdir', '/home/{}'.format(username)])
        container.attach_wait(lxc.attach_run_command, ['chown', '-R', username, '/home/{}'.format(username)])

        # Create the script to drop privileges on entrance
        container.attach_wait(lxc.attach_run_command, ['touch', '/bin/launch'])
        container.attach_wait(lxc.attach_run_command, ['chmod', '777', '/bin/launch'])
        with open(os.path.join(container.get_config_item('lxc.rootfs'), 'bin', 'launch'), 'wt') as f:
            f.write('#!/bin/sh' '\n\n' 'cd /home/{username}' '\n' 'su -c "$*" {username}'
                    .format(username=username))

        container.attach_wait(lxc.attach_run_command, ['chmod', '111', '/bin/launch'])


    def install_application(self, container, application, assume_yes=False):

        flags = []
        if assume_yes:
            flags += ['--assume-yes']

        container.attach_wait(lxc.attach_run_command, ['apt', 'update'])
        container.attach_wait(lxc.attach_run_command, ['apt', 'install'] + flags + [application])


    def upgrade(self, container, assume_yes=False):

        flags = []
        if assume_yes:
            flags += ['--assume-yes']

        assert(container.start())
        container.attach_wait(lxc.attach_run_command, ['apt', 'update'])
        container.attach_wait(lxc.attach_run_command, ['apt', 'upgrade'] + flags)
