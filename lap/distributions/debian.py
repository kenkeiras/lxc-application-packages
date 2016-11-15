# coding: utf-8

import lxc

from .debian_derived import *

class DebianStretch(DebianDerived):
    def __init__(self):
        DebianDerived.__init__(self, repositories=[
            DebianRepository('http://httpredir.debian.org/debian', 'stretch', ['main']),
            DebianRepository('http://security.debian.org/', 'stretch/updates', ['main']),
        ],
        identifier='debian.stretch')

    def create_instance(self, name):
        container = lxc.Container(name=name)
        container.create(template='download', args=('-d', 'debian',
                                                    '-r', 'stretch',
                                                    '-a', 'amd64'))
        return container


handler = DebianStretch()
