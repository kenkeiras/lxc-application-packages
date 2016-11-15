# coding: utf-8

import lxc
import yaml

import os
from os.path import expanduser

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


def save_to_registry(registry):
    os.makedirs(LOCAL_PATH, exist_ok=True)
    with open(CONTAINERS_REGISTRY_PATH, 'wt') as f:
        return f.write(yaml.dump(registry))


def deregister(application):
    registry = get_registry()
    del registry[application]
    save_to_registry(registry)


def register(container, distribution, application):
    registry = get_registry()
    registry[application] = {
        'container': {
            'name': container.name,
        },
        'distribution': {
            'name': distribution['name'],
        }
    }

    save_to_registry(registry)
