# coding: utf-8

import distributions as distros

def search(keywords,
           distribution=distros.DEBIAN,
           valid_keys=('Description', 'Tag', 'Section', 'Package')):

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
            print("{Package}: {Description}".format(**package))

    return results
