#!/usr/bin/env python3
# coding: utf-8

import os
import argparse

import search
import install
import run

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
    install_parser.add_argument('name',
                                type=str,
                                help='the application to be installed')

    # Run subparser
    run_parser = subparsers.add_parser('run', help='run a application')
    run_parser.add_argument('application',
                            type=str,
                            help='the application to be ran')

    return parser


def cli_search(args) -> int:
    results = search.search(keywords=args.keywords)
    ok = len(results) > 0
    return 0 if ok else 1

def cli_install(args) -> int:
    install.install(application=args.application)
    return 0

def cli_run(args) -> int:
    run.async_run(application=args.application)
    return 0


if __name__ == '__main__':
    parser = get_argparser()
    args = parser.parse_args()
    if args.command == 'search':
        retcode = cli_search(args)

    elif args.command == 'install':
        retcode = cli_install(args)

    elif args.command == 'run':
        retcode = cli_run(args)

    exit(retcode)
