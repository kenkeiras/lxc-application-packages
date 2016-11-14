# coding: utf-8

import lxc
import collection

def launch(args):
    return ["/bin/launch"] + args

def run(application, arguments):
    try:
        container = collection.get_container_from_application(application)
    except ContainerNotInstalledException as e:
        print("Application '{}' not found".format(e.args[0]))
        return 1

    container.start()
    return container.attach_wait(lxc.attach_run_command,
                                 launch([application] + list(arguments)))
