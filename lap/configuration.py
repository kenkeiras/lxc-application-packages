# coding: utf-8

from configparser import ConfigParser
import itertools
import os

def local_config_path(fname):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'config/',
                        fname)

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
