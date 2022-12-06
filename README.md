# 1Password backup and secure share split/combine scripts

## `1password-backup.py`

1password-backup.py is a Python 3 script for backing up all content accessible to a user in 1Password.

This script downloads all items and documents accessible to the 1Password user running the script, and saves them all in a compressed tar file, optionally public-key encrypted with gpg.

The script does not use any non-standard Python modules. It requires `op` (1Password CLI 2), `tar`, and `gpg` (if using the public-key encryption) in the search path.

Run the script with `--help` for additional information.

## `ssss-split-silent.py` and `ssss-combine-silent.py`

At Numerated, we don't want the encrypted backups we create with `1password-backup.py` to be decryptable by a single person. To solve this problem, we created a separate GPG keypair for the backups, gave its private key a long, random passphrase, and split that password into five shares using "ssss", a.k.a., [Shamir's Secret Sharing Scheme](http://point-at-infinity.org/ssss/).

However, there are two problems with this approach that ssss doesn't solve by itself:

1. the inception problem, i.e., how do you create the secret, split it into shares, and distribute those shares to the share-holders without anyone seeing the secret or multiple shares? and

2. the temporary use problem, i.e., how do you recreate the secret from shares and use it to decrypt a backup when you need to, without then needing to change the passphrase on the private key and distribute new shares to everyone?

The `ssss-split-silent.py` and `ssss-combine-silent.py` scripts do not _fully_ solve either of these problems, but they greatly facilitate their solution. They are wrappers around `ssss-split` and `ssss-combine` which allow a secret to be split into shares in separate files, and shares recombined into a secret, without any of them ever being visible on the terminal.

Below are two example scenarios for using these tools to solve the described problems. Both scenarios assume that the person performing the described steps is being observed by a second person to ensure that they don't peek.

### Example: key, passphrase, and share creation and distribution

1. Generate a long random passphrase and put it into a file without looking at it. For example, "`python3 -c 'import random; import string; import sys; sys.stdout.write("".join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=32)))' > passphrase.txt`".

2. Use "`gpg --generate-key`" to generate a new GPG key pair.

3. When prompted for the passphrase for the new key, in another window use `pbcopy`, `xclip`, `wl-copy`, or some other tool for your desktop OS to put the passphrase into the OS clipboard without looking at it, e.g., "`pbcopy < passphrase.txt`", then paste it into the dialog.

4. Make sure GPG doesn't remember the passphrase: "`gpg-connect-agent reloadagent /bye`".

5. Use `ssss-split-silent.py` to split the passphrase into shares as desired. For example, "`ssss-split-silent.py -t 2 -n 5 sharefile < passphrase.txt`" will create five shares in files named `sharefile1` through `sharefile2` and require two of them to reassemble the original passphrase.

6. Use some mechanism that allows you to upload and share files without looking at them to transmit the shares to the share-holders without looking at them. For example:

   * Upload the files into Google Drive, share each file with a different share-holder, tell them to copy the share from the file into a different, secure location, delete the shares from Google Drive, delete them from the Trash. (But beware! If your organization uses Google Vault these files will be accessible forever in Google Vault!)

   * Upload them into your password manager as attachments, share each with a different share-holder, delete them from the password manager when all the share-holders have copied them.

   * Etc.

### Example: temporary passphrase reassembly and usage

1. Set up a screen-share with enough share-holders to reassemble the passphrase, using a screen-sharing tool which allows any participant to take control of the shared screen, copy text from their local desktop, and paste it into the remote desktop. With Zoom, for example, the person sharing their screen needs to allow the shared clipboard by clicking "More > Remote Control > Share Clipboard" after giving remote control to another meeting attendee.

2. Use, for example, "`ssss-combine-silent.py -t 2 passphrasefile`" to reassemble the passphrase, giving remote control to each share-holder one at a time to copy and paste their share into the program (it will not be echoed).

3. Run `gpg` on whatever file requires the keypair. When it prompts for the passphrase, use `pbcopy` or whatever to copy the contents of the passphrase file into the clipboard and then paste it into the passphrase prompt.

4. Delete the passphrase file and Make GPG forget the passphrase: "`gpg-connect-agent reloadagent /bye`".

## Author

These scripts were written by Jonathan Kamens <<jik@kamens.us>> for Numerated Growth Technologies, Inc. Thanks to Numerated for open-sourcing the scripts.

## Copyright

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License (https://www.gnu.org/licenses/) for more details.
