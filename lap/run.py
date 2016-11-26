# coding: utf-8

import lxc
from . import collection

def launch(args):
    return ["/bin/launch"] + args

def run(application, arguments):
    try:
        container = collection.get_container_from_application(application)
    except collection.ContainerNotInstalledException as e:
        print("Application '{}' not found".format(e.args[0]))
        return 1

    container.start()
    command = collection.get_command_from_application(application)
    return container.attach_wait(lxc.attach_run_command,
                                 launch([command] + list(arguments)))


def upgrade(application, assume_yes=False):
    try:
        container = collection.get_container_from_application(application)
    except collection.ContainerNotInstalledException as e:
        print("Application '{}' not found".format(e.args[0]))
        return 1
    distro = collection.get_distribution_from_application(application)
    return distro['handler'].upgrade(container, assume_yes=assume_yes)
