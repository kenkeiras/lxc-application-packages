# coding: utf-8

from . import collection
from . import conversions

from configparser import ConfigParser
import itertools
import os
import string

def local_config_path(fname):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'config/',
                        fname)

DEFAULT_CONFIG_FILE = local_config_path('default.conf')
DEFAULT_GUI_CONFIG_FILE = local_config_path('gui_default.conf')


class RunningContainerException(Exception):
    pass


class Configuration:
    def __init__(self, configuration_file):
        self.parser = ConfigParser(strict=False)

        with open(configuration_file) as f:
            self.parser.read_file(itertools.chain(['[global]'], f),
                                  source=configuration_file)

        self.data = self.parser['global']

    @property
    def rootfs(self):
        return self.data['lxc.rootfs']

    @property
    def container_name(self):
        return self.data['lxc.utsname']

    @property
    def hwaddr(self):
        return self.data['lxc.network.hwaddr']

    @property
    def net_link(self):
        return self.data['lxc.network.link']

    @property
    def ipv4_addr(self):
        return self.data['lxc.network.ipv4']

    @property
    def ipv4_gateway(self):
        return self.data['lxc.network.ipv4.gateway']


def add_mount_point(application, host_directory, guest_directory):
    # Check the container is stopped
    container = collection.get_container_from_application(application)
    if container.state == 'RUNNING':
        raise RunningContainerException(application)

    # Register the mount point in the collection
    collection.register_mount_point(application, host_directory, guest_directory)

    # Regenerate the configuration
    application_settings = collection.get_registry()[application]
    configure(container,
              application_settings['configuration']['type'],
              application_settings['mount_points'])


def configure(container, distribution, app_config_file=DEFAULT_CONFIG_FILE, mount_points=[]):
    assert(container.save_config())

    config_file = os.path.join(container.get_config_path(),
                               container.name, 'config')
    config = Configuration(config_file)

    with open(app_config_file, 'rt') as f:
        template = string.Template(f.read())

    with open(config_file, 'wt') as f:
        # Write base template
        f.write(template.substitute(
            distro_name=distribution['lxc_name'],
            rootfs=config.rootfs,
            container_name=config.container_name,
            hwaddr=config.hwaddr,
            net_link=config.net_link,
            ipv4_addr=config.ipv4_addr,
            ipv4_gateway=config.ipv4_gateway,
        ))

        # Write mount points
        if len(mount_points) > 0:
            f.write('\n\n# Custom mount points\n')
            for guest_dir, host_dir in mount_points.items():
                f.write('lxc.mount.entry = {host_dir} {guest_dir} none bind,optional,create=dir\n'
                        .format(host_dir=conversions.to_fstab(host_dir),
                                guest_dir=conversions.to_fstab(guest_dir.strip('/')),
                        ))

    assert(container.load_config())
    return config
