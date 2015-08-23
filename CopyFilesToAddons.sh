#!/usr/bin/env bash

# To run this script from the terminal command line: ./CopyFilesToAddons.sh
# A Linux 'build' script. Run this after editing the addon's files. Then restart Anki. 
# Don't make edits over there in addons directly, as VCS won't see them, and an Anki or addon upgrade might destroy them.

# Copy recursively (-r) all modified files and folders, except the excluded ones
# (Like Anki's own deployment, this does NOT remove any files. The simplest way to do so manually here is to delete the addons folder, then re-run.)

mkdir -p ~/Anki/addons
rsync -r -u -v --exclude-from ExcludedFilesLinux.txt xml ~/Anki/addons/
rsync -r -u -v --exclude-from ExcludedFilesLinux.txt xpath ~/Anki/addons/
rsync -r -u -v --exclude-from ExcludedFilesLinux.txt distutils ~/Anki/addons/
rsync -r -u -v --exclude-from ExcludedFilesLinux.txt syncxml ~/Anki/addons/
cp -r -u -v syncx.py ~/Anki/addons/
