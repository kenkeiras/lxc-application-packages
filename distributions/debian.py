# coding: utf-8

from .debian_derived import *

class DebianStretch(DebianDerived):
    def __init__(self):
        DebianDerived.__init__(self, repositories=[
            DebianRepository('http://httpredir.debian.org/debian', 'stretch', ['main']),
            DebianRepository('http://security.debian.org/', 'stretch/updates', ['main']),
        ],
        identifier='debian.stretch')

handler = DebianStretch()
