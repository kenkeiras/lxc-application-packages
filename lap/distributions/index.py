# coding: utf-8

import string
from . import debian
DEBIAN = {
    'name': 'debian',
    'module': debian,
    'handler': debian.handler,
}


def get_map():
    distro_map = {}
    allowed = string.ascii_uppercase + '_'
    for distro in [distro
                   for distro
                   in dir()
                   if all(map(lambda x: x in allowed, distro))]:

        distro_map[distro['name']] = distro

    return distro_map
