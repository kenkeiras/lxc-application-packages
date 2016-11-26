# coding: utf-8

import string
from . import debian
DEBIAN = {
    'name': 'debian',
    'module': debian,
    'handler': debian.handler,
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
