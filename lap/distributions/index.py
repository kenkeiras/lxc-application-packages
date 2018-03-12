# coding: utf-8

import string
from . import debian_sid
from . import debian_stretch
DEBIAN = {
    'name': 'debian',
    'lxc_name': 'debian',
    'module': debian_sid,
    'handler': debian_sid.handler,
}

DEBIAN_STRETCH = {
    'name': 'debian_stretch',
    'lxc_name': 'debian_stretch',
    'module': debian_stretch,
    'handler': debian_stretch.handler,
}

from . import gentoo
GENTOO = {
    'name': 'gentoo',
    'lxc_name': 'gentoo',
    'module': gentoo,
    'handler': gentoo.handler,
}

from . import arch
ARCH = {
    'name': 'arch',
    'lxc_name': 'archlinux',
    'module': arch,
    'handler': arch.handler,
}

from . import fedora
FEDORA = {
    'name': 'fedora',
    'lxc_name': 'fedora',
    'module': fedora,
    'handler': fedora.handler,
}

allowed = string.ascii_uppercase + '_'
_locals = locals()
distros = [_locals[distro]
           for distro
           in dir()
           if all(map(lambda x: x in allowed, distro))]

def get_map():
    distro_map = {}
    for distro in distros:
        distro_map[distro['name']] = distro

    return distro_map
