# 1password-backup

Python 3 script for backing up all content accessible to a user in 1Password.

This script downloads all items and documents accessible to the 1Password user running the script, and saves them all in a compressed tar file, optionally public-key encrypted with gpg.

The script does not use any non-standard Python modules. It requires `op` (1Password CLI 2), `tar`, and `gpg` (if using the public-key encryption) in the search path.

Run the script with `--help` for additional information.

## Author

This script was written by Jonathan Kamens <<jik@kamens.us>> for Numerated Growth Technologies, Inc. Thanks to Numerated for open-sourcing the script.

## Copyright

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License (https://www.gnu.org/licenses/) for more details.
