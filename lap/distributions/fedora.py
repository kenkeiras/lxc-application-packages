# coding: utf-8

import lxc

from .redhat_derived import RedHatDerived
from .package_managers.dnf import DNFRepositoryMetalink

class Fedora24(RedHatDerived):
    def __init__(self):
        RedHatDerived.__init__(self, repositories=[
            DNFRepositoryMetalink('https://mirrors.fedoraproject.org/metalink',
                                  repo='fedora-source-24', architecture='x86_64'),
        ],
        identifier='fedora.24')

    def create_instance(self, name):
        container = lxc.Container(name=name)
        container.create(template='download', args=('-d', 'fedora',
                                                    '-r', '24',
                                                    '-a', 'amd64'))
        return container


handler = Fedora24()
