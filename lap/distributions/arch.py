# coding: utf-8

import lxc

from . import readers

import getpass
import re
import os.path
import hashlib
import requests
import tarfile
import json
import itertools

from os.path import expanduser
LOCAL_PATH = os.path.join(expanduser("~"), '.local', 'share', 'lap')


def build_hierarchy(tar_cache):
    members = tar_cache.getmembers()
    hierarchy = {}
    for member in members:
        path = member.path.split('/')
        leaf = hierarchy
        for p in path:
            if p not in leaf:
                leaf[p] = {}
            leaf = leaf[p]

        leaf['_'] = member

    return hierarchy


def parse_data_from_element(tar_info, cache):
    data = cache.extractfile(tar_info).read().decode('utf-8')
    metadata = {}

    key = None
    value = ''
    for line in data.split('\n'):
        if line.startswith('%'):
            if key is not None:
                metadata[key] = value
            key = line.strip('%')
            value = ''
        else:
            value += ' ' + line

    if key is not None:
        metadata[key] = value

    return metadata


def parse_dependencies(deps):
    result = []
    for dep in deps.split():
        result.append(dep.split('>')[0].split('=')[0].split('<')[0])

    return result



def parse_package(package, hierarchy, cache):
    metadata = {}
    for element in hierarchy[package]:
        if element == '_':
            continue

        data = parse_data_from_element(hierarchy[package][element]['_'],
                                       cache)
        for key, value in data.items():
            metadata[key] = value

    if 'GROUPS' in metadata:
        metadata['Section'] = metadata['GROUPS'].strip()
    metadata['Package'] = metadata['NAME'].strip()

    if 'DEPENDS' in metadata:
        metadata['Depends'] = parse_dependencies(metadata['DEPENDS'].strip())

    metadata['Description'] = metadata['DESC'].strip()

    if 'PROVIDES' in metadata:
        metadata['Provides'] = parse_dependencies(metadata['PROVIDES'].strip())
    yield metadata


def get_packages(hierarchy, cache):
    for package in hierarchy:
        yield from parse_package(package, hierarchy, cache)


def build_provides_map(pkg_map):
    provides_map = {}
    for name, pkg in pkg_map.items():
        if 'Provides' in pkg:
            for element in pkg['Provides']:
                if element not in provides_map:
                    provides_map[element] = []
                provides_map[element].append(pkg)
    return provides_map


class ArchCacheReader():
    def __init__(self, repos, identifier):
        assert(len(repos) > 0)

        self.cache_paths = []
        for repo in repos:
            cache_dir = get_cache_path(identifier)
            cache_file = 'arch-{repository}.tar'.format(repository=repo.repository)
            self.cache_paths.append(os.path.join(cache_dir, repo.identifier, cache_file))

        self.caches = [tarfile.open(cache_path) for cache_path in self.cache_paths]

    def get_packages(self):
        for cache in self.caches:
            hierarchy = build_hierarchy(cache)
            yield from get_packages(hierarchy, cache)


class ArchRepository():
    def __init__(self, uri='https://mirrors.kernel.org/archlinux/', repository='latest'):
        self.uri = uri
        self.repository = repository
        self.identifier = (uri.replace('/', '_')
                           .replace('.', '_')
                           .replace(':', '_')
                           + '-' + repository)

    def download_to(self, dir_name):
        os.makedirs(dir_name, exist_ok=True)
        cache_file_name = os.path.join(dir_name,
                                       'arch-{repository}.tar'
                                       .format(repository=self.repository))

        if os.path.exists(cache_file_name):
            return

        base_url = ('{uri}/{repository}/os/x86_64/{repository}.db.tar.gz'
                    .format(uri=self.uri,
                            repository=self.repository))
        print("Downloading {} to {}...".format(base_url, cache_file_name), end='', flush=True)
        with open(cache_file_name, 'wb') as f:
            r = requests.get(base_url)
            f.write(readers.gz(r.content))
        print("\b\b\b OK")


def get_cache_path(identifier):
    return os.path.join(LOCAL_PATH, 'cache', identifier + '.cache')


def build_cache(repositories, identifier):
    cache_dir = get_cache_path(identifier)
    os.makedirs(cache_dir, exist_ok=True)
    for repo in repositories:
        repo.download_to(os.path.join(cache_dir, repo.identifier))

class ArchCurrent():
    GRAPHICAL_APP_REQUIREMENTS = ['x11-common', 'libx11-data', 'libdrm2']

    def __init__(self):
        self.repositories = [
            ArchRepository(repository='core'),
            ArchRepository(repository='extra'),
            ArchRepository(repository='community'),
            ArchRepository(repository='multilib'),
        ]
        self.identifier = 'arch.current'

    def get_packages(self):
        build_cache(self.repositories, self.identifier)
        reader = ArchCacheReader(self.repositories, self.identifier)
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
        provides_index = build_provides_map(pkg_map)
        dependencies = [application]
        checked = set()
        while len(dependencies) > 0:
            next_dep = dependencies.pop()
            if next_dep in pkg_map:
                dep = pkg_map[next_dep]
            else:
                dep = provides_index[next_dep][0]

            if 'Depends' not in dep:
                continue

            subdeps = dep['Depends']
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


    def create_instance(self, name):
        container = lxc.Container(name=name)
        container.create(template='download', args=('-d', 'archlinux',
                                                    '-r', 'current',
                                                    '-a', 'amd64'))
        return container


    def install_application(self, container, application, assume_yes=False):
        flags = []
        if assume_yes:
            flags.append('--noconfirm')

        container.attach_wait(lxc.attach_run_command, ['pacman', '-Sy'])
        container.attach_wait(lxc.attach_run_command, ['pacman', '-S'] + flags + [application])

    def upgrade(self, container, assume_yes=False):

        flags = []
        if assume_yes:
            flags += ['--noconfirm']

        assert(container.start())
        container.attach_wait(lxc.attach_run_command, ['pacman', '-Syu'] + flags)


handler = ArchCurrent()
