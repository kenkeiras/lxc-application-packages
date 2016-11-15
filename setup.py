from setuptools import setup

setup(name='lap',
      version='0.1',
      description='Python scripts to use LXC as a simplistic package manager.',
      url='https://github.com/kenkeiras/lxc-application-packages',
      author='kenkeiras',
      author_email='kenkeiras@codigoparallevar.com',
      license='MIT',
      packages=['lap'],
      scripts=['bin/lap'],
      include_package_data=True,
      install_requires = [
          'requests',
          'PyYAML',
          'lxc',
      ],
      zip_safe=False)
