#!/usr/bin/env python3

# Combine a secret without seeing the secret or its shares.

# The goal is to allow the resulting shares to be distributed to the
# share-holders without any of them seeing the others' shares or the original
# key. How to distribute the share files is a problem to be solved outside the
# scope of this script.

# Accepts the same arguments as ssss-split (see
# http://point-at-infinity.org/ssss/), with the exception of -q, -Q, -D, and
# -v.

# Accepts one additional mandatory positional argument, an output file name.
# You can specify "-" as the output file name to send the combined secret to
# stdout, but in that case make sure you redirect stdout somewhere or you'll
# partially defeat the purpose of the script!

# Accepts on additional optional argument, "-i share_file" to read a share from
# the specified file. Specify multiple times to read multiple shares from
# files.

# Reads the specified share files if any, then reads one share per line from
# the terminal or stdin with echo off on the terminal. Then calls ssss-combine
# and with the other specified command-line arguments, feeds the shares into
# it, and sends the combined secret to the specified output file name.

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
    parser = argparse.ArgumentParser(description='Call ssss-combine silently.')
    parser.add_argument('-t', dest='threshold', required=True, action='store',
                        type=int, help='Specify the number of shares '
                        'necessary to reconstruct the secret.')
    parser.add_argument('-x', dest='hex_mode', action='store_true',
                        help='Hex mode: use hexadecimal digits in place of '
                        'ASCII characters for I/O.')
    parser.add_argument('-i', dest='input_file', action='append', default=[],
                        help='Read a share from the specified file.')
    parser.add_argument('output_file', metavar='OUTPUT_FILE',
                        help='File name to save secret in.')
    return parser.parse_args()


def main():
    args = parse_args()
    if os.path.exists(args.output_file):
        sys.exit(f'Will not overwrite existing file {args.output_file}')
    if len(args.input_file) > args.threshold:
        sys.exit(f'Too many input files specified (max {args.threshold})')
    shares = []
    for file_name in args.input_file:
        shares.append(open(file_name).read().strip())
    while len(shares) < args.threshold:
        if sys.stdin.isatty():
            share = getpass.getpass('')
        else:
            share = input('')
        shares.append(share)
    command = ['ssss-combine', '-q', '-t', str(args.threshold)]
    if args.hex_mode:
        command.append('-x')
    result = subprocess.run(command, input='\n'.join(shares) + '\n', text=True,
                            capture_output=True, check=True)
    secret = result.stderr.strip()
    if args.output_file == '-':
        print(secret)
    else:
        with open(args.output_file, 'w') as f:
            f.write(secret)


if __name__ == '__main__':
    main()
