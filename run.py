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

def launch(args):
    return ["/bin/launch"] + args

def run(application, arguments):
    try:
        container = get_container_from_application(application)
    except ContainerNotInstalledException as e:
        print("Application '{}' not found".format(e.args[0]))
        return 1

    return container.attach_wait(lxc.attach_run_command,
                                 launch([application] + list(arguments)))
