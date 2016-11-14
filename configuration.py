# coding: utf-8

from configparser import ConfigParser
import itertools

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
