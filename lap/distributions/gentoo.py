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


def get_categories(portage_tree):
    categories = []
    for element in portage_tree.keys():
        parts = element.split('-')
        if len(parts) == 2 and len(parts[0]) == 3:
            categories.append(element)
    return categories


class VersionNum:
    __slots__ = ['num']
    def __init__(self, num):
        self.num = num

    def __lt__(self, other):
        if isinstance(other, VersionNum):
            return self.num < other.num
        else:
            return False

    def __gt__(self, other):
        if isinstance(other, VersionNum):
            return self.num > other.num
        else:
            return True

    def __eq__(self, other):
        if isinstance(other, VersionNum):
            return self.num == other.num
        else:
            return False

    def __le__(self, other):
        if isinstance(other, VersionNum):
            return self.num <= other.num
        else:
            return False

    def __ge__(self, other):
        if isinstance(other, VersionNum):
            return self.num >= other.num
        else:
            return True

    def __ne__(self, other):
        if isinstance(other, VersionNum):
            return self.num != other.num
        else:
            return True


def version_to_key(version):
    parts1 = version.split('-')
    parts2 = [part.split('.') for part in parts1]
    for super_part in parts2:
        for i, subpart in enumerate(super_part):
            if subpart.isdigit():
                super_part[i] = VersionNum(int(subpart))

    return list(itertools.chain(*parts2))

def version_sort(versions, reverse):
    '''
    Sorts a series of strings using the adecuate version semantics.

    assertEqual(version_sort(['gutenprint-5.2.9.ebuild', 'gutenprint-5.2.11.ebuild', 'gutenprint-5.2.10.ebuild'], reverse=True),
                             ['gutenprint-5.2.11.ebuild', 'gutenprint-5.2.10.ebuild', 'gutenprint-5.2.9.ebuild'])
    '''
    return sorted(versions, key=version_to_key, reverse=reverse)


def parse_value(value):
    has_to_continue = False # TODO
    return has_to_continue, value


def read_data(data):
    values = {}

    reader = iter(data.split('\n'))
    for line in reader:
        if len(line) > 0 and line[0] != ' ' and '=' in line:
            key, value = line.split('=', 1)
            has_to_continue, value = parse_value(value)
            # TODO continue
            values[key.capitalize()] = value

    return values


def read_package(portage_tree, category, element, cache):
    ebuilds = version_sort([f
                            for f in portage_tree[category][element]
                            if f.endswith('.ebuild')],
                           reverse=True)
    assert(len(ebuilds) > 0)
    data = cache.extractfile(portage_tree[category][element][ebuilds[0]]['_']).read()

    data = read_data(data.decode('utf-8'))
    data['Section'] = category
    data['Package'] = element

    return data


def get_packages_by_category(portage_tree, categories, cache):
    for category in categories:
        for element in portage_tree[category].keys():
            if element in ('metadata.xml', '_'):
                continue
            yield read_package(portage_tree, category, element, cache)

class GentooCacheReader():
    def __init__(self, repos, identifier, version='latest'):
        assert(len(repos) == 1)

        cache_dir = get_cache_path(identifier)
        cache_file = 'portage-{version}.tar'.format(version=version)

        self.cache_path = os.path.join(cache_dir, repos[0].identifier, cache_file)
        self.cache = tarfile.open(self.cache_path)

    def get_packages(self):
        hierarchy = build_hierarchy(self.cache)
        portage = hierarchy['portage']
        categories = get_categories(portage)
        yield from get_packages_by_category(portage, categories, self.cache)

class GentooRepository():
    def __init__(self, uri='http://distfiles.gentoo.org', version='latest'):
        self.uri = uri
        self.version = version
        self.identifier = (uri.replace('/', '_')
                           .replace('.', '_')
                           .replace(':', '_')
                           + '-' + version)

    def download_to(self, dir_name):
        os.makedirs(dir_name, exist_ok=True)
        cache_file_name = os.path.join(dir_name,
                                       'portage-{version}.tar'.format(version=self.version))

        if os.path.exists(cache_file_name):
            return

        base_url = ('{uri}/snapshots/portage-{version}.tar'
                    .format(uri=self.uri,
                            version=self.version))
        for (extension, reader) in (('.xz', readers.xz), ('.bz2', readers.bz),
                                    ('.gz', readers.gz), ('', readers.plain)):
            print("Downloading {} to {}...".format(base_url + extension, cache_file_name), end='', flush=True)
            with open(cache_file_name, 'wb') as f:
                r = requests.get(base_url + extension)
                f.write(reader(r.content))
            print("\b\b\b OK")
            break #@TODO: WTF?!




def get_cache_path(identifier):
    return os.path.join(LOCAL_PATH, 'cache', identifier + '.cache')


def build_cache(repositories, identifier):
    cache_dir = get_cache_path(identifier)
    os.makedirs(cache_dir, exist_ok=True)
    for repo in repositories:
        repo.download_to(os.path.join(cache_dir, repo.identifier))

class GentooCurrent():
    def __init__(self):
        self.version = 'latest'
        self.repositories = [GentooRepository(version=self.version)]
        self.identifier = 'gentoo.current'

    def get_packages(self):
        build_cache(self.repositories, self.identifier)
        reader = GentooCacheReader(self.repositories, self.identifier, self.version)
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

        # Configure the network
        container.attach_wait(lxc.attach_run_command, ['chmod', '777', '/etc/conf.d/net'])
        with open(os.path.join(container.get_config_item('lxc.rootfs'), 'etc', 'conf.d', 'net'), 'wt') as f:
            f.write('rc_keyword="-stop"\n')
            f.write('config_eth0="{ipv4_addr}"\n'.format(ipv4_addr=configuration.ipv4_addr))
            f.write('routes_eth0="default via {ipv4_gateway}"\n'.format(ipv4_gateway=configuration.ipv4_gateway))

        container.attach_wait(lxc.attach_run_command, ['chmod', '444', '/etc/conf.d/net'])

        # Create the script to drop privileges on entrance
        container.attach_wait(lxc.attach_run_command, ['touch', '/bin/launch'])
        container.attach_wait(lxc.attach_run_command, ['chmod', '777', '/bin/launch'])
        with open(os.path.join(container.get_config_item('lxc.rootfs'), 'bin', 'launch'), 'wt') as f:
            f.write('#!/bin/sh' '\n\n' 'cd /home/{username}' '\n' 'su -c "$*" {username}'
                    .format(username=username))

        container.attach_wait(lxc.attach_run_command, ['chmod', '111', '/bin/launch'])


    def create_instance(self, name):
        container = lxc.Container(name=name)
        container.create(template='download', args=('-d', 'gentoo',
                                                    '-r', 'current',
                                                    '-a', 'amd64'))
        return container


    def install_application(self, container, application, assume_yes=False):
        flags = []
        if assume_yes:
            pass

        container.attach_wait(lxc.attach_run_command, ['emerge', '--sync'])
        container.attach_wait(lxc.attach_run_command, ['emerge'] + flags + [application])


handler = GentooCurrent()
