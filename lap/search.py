# coding: utf-8

from . import distributions as distros
from . import collection

def search(keywords,
           distribution=distros.GENTOO,
           valid_keys=('Description', 'Tag', 'Section', 'Package')):

    installed_apps = collection.get_installed_apps()
    distro = distros.get_handler(distribution)
    results = []
    for package in distro.get_packages():
        for kw in keywords:
            kw = kw.lower()
            found = any([
                (kw in value.lower())
                for key, value
                in package.items()
                if key in valid_keys
            ])

            if not found:
                break
        else:
            results.append(package)

            marks = ''
            if package['Package'] in installed_apps:
                marks = '[installed]'
            print("{Package}: {Description} {marks}".format(**package, marks=marks))

    return results
