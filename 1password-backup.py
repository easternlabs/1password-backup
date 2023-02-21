#!/usr/bin/env python3

# Script for backing up 1Password items and documents
#
# Requires `op` (1Password CLI), `tar`, and (optionally) `gpg` in search path.
# Run with `--help` for more information about usage.
#
# Copyright 2021-2022 Numerated Growth Technologies, Inc.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License
# (https://www.gnu.org/licenses/) for more details.

import argparse
from collections import defaultdict
import json
import os
import random
import re
import subprocess
import sys
import tempfile


def parse_args():
    parser = argparse.ArgumentParser(description='Back up 1Password')
    parser.add_argument('--verbose', action='store_true', default=False,
                        help='Generate more verbose output including progress')
    parser.add_argument('--force', action='store_true', default=False,
                        help='Overwrite existing output files')
    parser.add_argument('--signin', action=argparse.BooleanOptionalAction,
                        default=True, help='Sign into 1Password CLI '
                        '(default yes)')
    parser.add_argument('--private', action=argparse.BooleanOptionalAction,
                        default=True, help='Include Private vault in backup '
                        '(default yes)')
    parser.add_argument('--encrypt', action='store_true', default=False,
                        help='Encrypt backup file with "gpg --encrypt" and '
                        'delete unencrypted file')
    parser.add_argument('--key', action='store', help='GPG key to use for '
                        'encryption instead of the default (implies '
                        '--encrypt)')
    parser.add_argument('--backup-percentage', type=int, action='store',
                        help='Backup approximately the specified percentage '
                        'of all items and documents rather than all of them, '
                        'for testing and debugging')
    parser.add_argument('output_file', metavar='output-file',
                        help='File to put backup in (".tar" suffix will be '
                        'added if file name doesn\'t end in ".tar" or ".tgz")')
    args = parser.parse_args()
    if not re.match(r'.*\.(?:tar|tgz)$', args.output_file, re.IGNORECASE):
        args.output_file += '.tar'
    if not args.output_file.startswith('/'):
        args.output_file = f'{os.getcwd()}/{args.output_file}'
    if args.backup_percentage is not None and \
       (args.backup_percentage < 0 or args.backup_percentage > 100):
        parser.exit(f'Backup percentage {args.backup_percentage} is not '
                    'between 0 and 100')
    if args.key:
        args.encrypt = True
    if args.encrypt:
        args.encrypted_output_file = f'{args.output_file}.gpg'
    if not args.force:
        if os.path.exists(args.output_file):
            parser.exit(f'Output file {args.output_file} already '
                        'exists; specify "--force" to overwrite')
        if args.encrypt and os.path.exists(args.encrypted_output_file):
            parser.exit(f'Output file {args.encrypted_output_file} already '
                        'exists; specify "--force" to overwrite')
    return args


def download_category(args, category, skip_vaults, vault_names):
    result = subprocess.run(('op', 'list', category),
                            stdout=subprocess.PIPE, check=True)
    items = json.loads(result.stdout)
    items = [i for i in items if i['vaultUuid'] not in skip_vaults]
    if args.backup_percentage:
        items = random.choices(
            items, k=int(args.backup_percentage * len(items) / 100))
    vault_to_items = defaultdict(list)
    for i in items:
        vault_to_items[i['vaultUuid']].append(i)
    item_count = 0
    item_total_count = len(items)
    category = 'item' if category == "items" else "document"
    for vault, vault_items in vault_to_items.items():
        vault_outdir = f'{vault_names[vault]}/{category}s'
        os.makedirs(vault_outdir, exist_ok=True)
        with open(f'{vault_outdir}.json', 'w') as f:
            json.dump(vault_items, f, indent=2)
        for i in vault_items:
            uuid = i['uuid']
            title = i['overview']['title'].replace('/', '_')
            item_outdir = f'{vault_outdir}/{uuid}'
            os.makedirs(item_outdir, exist_ok=True)
            outfile = f'{item_outdir}/{title}'
            with open(outfile, 'wb') as f:
                result = subprocess.run(
                    ('op', 'get', category, uuid, '--vault', vault),
                    stdout=subprocess.PIPE, check=True)
                f.write(result.stdout)
            item_count += 1
            if args.verbose:
                print(f'Downloaded {item_count}/{item_total_count} '
                      f'{category}s')


def download_all(args, skip_vaults, vault_names):
    for category in ('items', 'documents'):
        download_category(args, category, skip_vaults, vault_names)


def main():
    args = parse_args()
    os.environ['OP_FORMAT'] = 'json'
    skip_vaults = set()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        if args.signin:
            result = subprocess.run(('op', 'signin'), encoding='utf-8',
                                    stdout=subprocess.PIPE, check=True)
            match = re.match(r'export (.*)="(.*)"', result.stdout)
            if not match:
                sys.exit(f'Could not find token name and value in op signin '
                         f'output:\n{result.stdout}')
            os.environ[match.group(1)] = match.group(2)
        result = subprocess.run(('op', 'list', 'vaults'), encoding='utf-8',
                                stdout=subprocess.PIPE, check=True)
        vaults = json.loads(result.stdout)
        if not args.private:
            skip_vaults.update((v['uuid'] for v in vaults
                                if v['name'] == 'Private'))
            vaults = [v for v in vaults if v['name'] != 'Private']
        with open('vaults.json', 'w') as f:
            json.dump(vaults, f, indent=2)
        uuid_to_vault = {}
        vault_to_uuid = {}
        for v in vaults:
            use_name = v['name'].replace('/', '_')
            if v['name'] in vault_to_uuid:
                use_name = f'{use_name} {v["uuid"]}'
                print(f'Warning: duplicate vault name {v["name"]}; '
                      f'renaming to {use_name}')
            uuid_to_vault[v['uuid']] = use_name
            vault_to_uuid[use_name] = v['uuid']
        download_all(args, skip_vaults, uuid_to_vault)
        subprocess.run(('tar', '-c', '-z', '-f', args.output_file, '.'),
                       check=True)
        if args.encrypt:
            cmd = ['gpg', '--batch', '--encrypt']
            if args.force:
                cmd.append('--yes')
            if args.key:
                # The documentation claims only --local-user is necessary but
                # in my real-world experience --default-key is definitely
                # necessary and --local-user may be as well, so I include both
                # here.
                cmd.extend(['--default-key', args.key,
                            '--local-user', args.key,
                            '--recipient', args.key])
            cmd.append(args.output_file)
            subprocess.run(cmd, check=True)
            os.unlink(args.output_file)


if __name__ == '__main__':
    main()
