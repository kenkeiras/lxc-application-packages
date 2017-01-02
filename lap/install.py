# coding: utf-8

import lxc
from . import distributions as distros
from . import configuration
from . import collection

import os
import random
import string

RANDOM_NAME_LENGTH = 10

def generate_random_name(length=RANDOM_NAME_LENGTH):
    chunks = []
    for _ in range(length):
        chunks.append(random.choice(string.ascii_lowercase))
    return ''.join(chunks)


def get_available_name_from_base(name_base):
    name = 'lap-{}'.format(name_base)
    containers = lxc.list_containers()
    if name in containers:
        i = 2
        while '{name}-{i}'.format(name=name, i=i) in containers:
            i += 1
        name = '{name}-{i}'.format(name=name, i=i)
    return name


def create_lxc_instance(distribution, name_base=None):
    if name_base is None:
        name_base = generate_random_name()

    name = get_available_name_from_base(name_base)
    print('Creating container {}'.format(name))
    container = distribution['handler'].create_instance(name)
    return container


def reload_container(container):
    return lxc.Container(container.name)


def pick_configuration(distribution, application):
    distro = distribution['handler']
    if distro.is_graphical(application):
        print('Installing as graphical application')
        return configuration.DEFAULT_GUI_CONFIG_FILE
    else:
        return configuration.DEFAULT_CONFIG_FILE


def uninstall(application):
    try:
        container = collection.get_container_from_application(application)
    except collection.ContainerNotInstalledException as e:
        print("Application '{}' not found".format(e.args[0]))
        return 1

    assert(container.stop())
    assert(container.destroy())
    collection.deregister(application)
    return 0


def install(application, name=None, distribution=distros.GENTOO, assume_yes=False):
    if name is None:
        name = application

    if not distribution['handler'].has_application(application):
        print("Distribution {} doesn't have the application {}"
              .format(distribution['name'], application))
        return 1

    try:
        container = create_lxc_instance(distribution, name_base=name)
        configuration_type = pick_configuration(distribution, application)
        collection.register(container, distribution, name, application,
                            configuration={'type': configuration_type})

        config = configuration.configure(container, distribution, app_config_file=configuration_type)
        container = reload_container(container)

        assert(container.start())
    except AssertionError as e:
        container.destroy()
        raise

    distribution['handler'].configure_first_time(container, config)
    container.stop()
    assert(container.start())
    distribution['handler'].install_application(container, application, assume_yes=assume_yes)
    return 0
