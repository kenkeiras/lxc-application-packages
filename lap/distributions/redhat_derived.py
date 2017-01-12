# coding: utf-8

import os
import lxc

from .package_managers.dnf import build_cache, DNFCacheReader

import getpass

class RedHatDerived:
    GRAPHICAL_APP_REQUIREMENTS = ['x11-common', 'libx11-data', 'libdrm2']

    def __init__(self, repositories, identifier):
        self.repositories = repositories
        self.identifier = identifier

    def get_packages(self):
        build_cache(self.repositories, self.identifier)
        reader = DNFCacheReader(self.repositories, self.identifier)
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
            flags += ['-y']

        assert(container.start())
        container.attach_wait(lxc.attach_run_command, ['dnf', 'install'] + flags + [application])


    def upgrade(self, container, assume_yes=False):

        flags = []
        if assume_yes:
            flags += ['-y']

        assert(container.start())
        container.attach_wait(lxc.attach_run_command, ['dnf', 'upgrade'] + flags)
