# coding: utf-8

import lxc
import yaml

import os
from os.path import expanduser

from . import distributions as distros

LOCAL_PATH = os.path.join(expanduser("~"), '.local', 'share', 'lap')
CONTAINERS_REGISTRY_PATH = os.path.join(LOCAL_PATH, 'containers.yml')

class ContainerNotInstalledException(Exception):
    pass

def get_registry():
    if os.path.exists(CONTAINERS_REGISTRY_PATH):
        with open(CONTAINERS_REGISTRY_PATH, 'rt') as f:
            return yaml.load(f.read())
    return {}


def get_container_from_application(application):
    registry = get_registry()
    if application not in registry:
        raise ContainerNotInstalledException(application)
    return lxc.Container(registry[application]['container']['name'])


def get_command_from_application(application):
    registry = get_registry()
    if application not in registry:
        raise ContainerNotInstalledException(application)
    return registry[application]['application']['name']


def get_installed_apps():
    registry = get_registry()
    return set([app['application']['name'] for _name, app in registry.items()])


def get_distribution_from_application(application):
    registry = get_registry()
    if application not in registry:
        raise ContainerNotInstalledException(application)
    distro = registry[application]['distribution']['name']
    return distros.get_map()[distro]


def save_to_registry(registry):
    os.makedirs(LOCAL_PATH, exist_ok=True)
    with open(CONTAINERS_REGISTRY_PATH, 'wt') as f:
        return f.write(yaml.dump(registry))


def deregister(application):
    registry = get_registry()
    del registry[application]
    save_to_registry(registry)


def register(container, distribution, name, application, configuration={}):
    registry = get_registry()
    registry[name] = {
        'container': {
            'name': container.name,
        },
        'distribution': {
            'name': distribution['name'],
        },
        'application': {
            'name': application,
        },
        'mount_points': {},
        'configuration': configuration
    }


    save_to_registry(registry)

def register_mount_point(application, host_dir, guest_dir):
    registry = get_registry()
    registry[application]['mount_points'][guest_dir] = host_dir
    save_to_registry(registry)
