# coding: utf-8

def to_fstab(path):
    '''Convert the path into a fstab-compatible one.'''
    not_allowed = '\n\t \r'

    def clean_char(c):
        '''Check if the character is allowed, if not return it's octal
        representation.'''
        if c in not_allowed:
            return oct(ord(c)).replace('0o', '\\0')
        return c

    return ''.join([clean_char(c) for c in path])
