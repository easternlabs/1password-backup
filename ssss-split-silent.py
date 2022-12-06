#!/usr/bin/env python3

# Split a secret without seeing the secret or its shares.

# The goal is to allow the resulting shares to be distributed to the
# share-holders without any of them seeing the others' shares or the original
# key. How to distribute the share files is a problem to be solved outside the
# scope of this script.

# Accepts the same arguments as ssss-split (see
# http://point-at-infinity.org/ssss/), with the exception of -q, -Q, -D, and
# -v. Accepts one additional mandatory positional argument, an output file
# prefix. Reads the secret on stdin with no prompt after turning off echo on
# the terminal, then calls ssss-split on it with the other specified
# command-line arguments, reads the output from ssss-split, and saves each
# share into a separate numbered file whose name started with the specified
# prefix.

# Copyright 2022 Numerated Growth Technologies, Inc.

# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License
# (https://www.gnu.org/licenses/) for more details.

import argparse
import getpass
import os
import subprocess
import sys


def parse_args():
    parser = argparse.ArgumentParser(description='Call ssss-split silently.')
    parser.add_argument('-t', dest='threshold', required=True, action='store',
                        type=int, help='Specify the number of shares '
                        'necessary to reconstruct the secret.')
    parser.add_argument('-n', dest='shares', required=True, action='store',
                        type=int, help='Specify the number of shares to be '
                        'generated.')
    parser.add_argument('-w', dest='token', action='store', help='Text token '
                        'to name shares in order to avoid confusion in case '
                        'one utilizes secret sharing to protect several '
                        'independent secrets.')
    parser.add_argument('-s', dest='level', type=int, help="Enforce the "
                        "scheme's security level (in bits).")
    parser.add_argument('-x', dest='hex_mode', action='store_true',
                        help='Hex mode: use hexadecimal digits in place of '
                        'ASCII characters for I/O.')
    parser.add_argument('output_prefix', metavar='OUTPUT_PREFIX',
                        help='Name prefix for files to save shares in.')
    return parser.parse_args()


def main():
    args = parse_args()
    file_names = [f'{args.output_prefix}{i + 1}' for i in range(args.shares)]
    for file_name in file_names:
        if os.path.exists(file_name):
            sys.exit(f'Will not overwrite existing file {file_name}')
    if sys.stdin.isatty():
        secret = getpass.getpass('')
    else:
        secret = input('')
    command = ['ssss-split', '-q', '-t', str(args.threshold),
               '-n', str(args.shares)]
    if args.token:
        command.extend(('-w', args.token))
    if args.level:
        command.extend(('-s', str(args.level)))
    if args.hex_mode:
        command.append('-x')
    result = subprocess.run(command, input=secret, text=True,
                            capture_output=True, check=True)
    shares = result.stdout.strip().split('\n')
    if len(shares) != args.shares:
        sys.exit(f'ERROR: Expected {args.shares} shares, got {len(shares)}')
    for i in range(len(shares)):
        share = shares[i]
        file_name = file_names[i]
        with open(file_name, 'w') as f:
            f.write(share)


if __name__ == '__main__':
    main()
