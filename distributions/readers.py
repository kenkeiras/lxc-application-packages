# coding: utf-8

import lzma
import bz2
import gzip

def xz(data):
    return lzma.decompress(data)

def bz(data):
    return bz2.decompress(data)

def gz(data):
    return gzip.decompress(data)

def plain(data):
    return data
