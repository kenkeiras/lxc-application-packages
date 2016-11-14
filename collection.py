# coding: utf-8

import lxc

class ContainerNotInstalledException(Exception):
    pass

def get_container_from_application(application):
    name = 'lap-{application}'.format(application=application)
    containers = lxc.list_containers()
    if name not in containers:
        raise ContainerNotInstalledException(application)
    return lxc.Container(name)
