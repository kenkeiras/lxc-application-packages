#!/usr/bin/env python3
# coding: utf-8

import os
import argparse

import search
import install
import run
import collection

def get_argparser() -> argparse.ArgumentParser:
    # Base  parser
    parser = argparse.ArgumentParser(
        description='use lxc to install isolated applications')
    subparsers = parser.add_subparsers()
    subparsers.required = True
    subparsers.dest = 'command'

    # Search subparser
    search_parser = subparsers.add_parser(
        'search',
        help='search in the available applications')
    search_parser.add_argument('keywords',
                               type=str,
                               nargs='+',
                               help='the keywords to search')

    # Build subparser
    install_parser = subparsers.add_parser(
        'install',
        help='install a new application')
    install_parser.add_argument('-y', '--assume-yes',
                                action='store_true',
                                help='assume `yes` on the installation decisions')

    install_parser.add_argument('-n', '--name',
                                type=str,
                                nargs='?',
                                help='name given to the application')

    install_parser.add_argument('application',
                                type=str,
                                help='the application to be installed')

    # Remove subparser
    uninstall_parser = subparsers.add_parser(
        'uninstall',
        help='remove a installed application')
    uninstall_parser.add_argument('application',
                                type=str,
                                help='the application to be removed')

    # Run subparser
    run_parser = subparsers.add_parser('run', help='run a application')
    run_parser.add_argument('application',
                            type=str,
                            help='the application to be ran')

    run_parser.add_argument('arguments',
                            type=str,
                            nargs='*',
                            help='the application arguments')

    # List subparser
    list_parser = subparsers.add_parser('list', help='list installed applications')


    return parser


def cli_search(args) -> int:
    results = search.search(keywords=args.keywords)
    ok = len(results) > 0
    return 0 if ok else 1

def cli_install(args) -> int:
    install.install(application=args.application, name=args.name,
                    assume_yes=args.assume_yes)
    return 0

def cli_uninstall(args) -> int:
    install.uninstall(application=args.application)
    return 0

def cli_run(args) -> int:
    run.run(application=args.application, arguments=args.arguments)
    return 0


def cli_list(args) -> int:
    for name, app in collection.get_registry().items():
        print("{name} [{appname}][{container_name}]"
              .format(name=name,
                      appname=app['application']['name'],
                      container_name=app['container']['name']
              ))
    return 0


if __name__ == '__main__':
    parser = get_argparser()
    args = parser.parse_args()
    if args.command == 'search':
        retcode = cli_search(args)

    elif args.command == 'install':
        retcode = cli_install(args)

    elif args.command == 'uninstall':
        retcode = cli_uninstall(args)

    elif args.command == 'run':
        retcode = cli_run(args)

    elif args.command == 'list':
        retcode = cli_list(args)

    exit(retcode)
