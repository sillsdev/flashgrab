#!/usr/bin/env bash

# To run this script from the terminal command line: ./CopyFilesToAddons.sh
# A Linux 'build' script. Run this after editing the addon's files. Then restart Anki.
# Don't make edits over there in addons directly, as VCS won't see them, and an Anki or addon upgrade might destroy them.

# IMPORTANT: If you change the plugin package in manifest.json, make the same change to PLUGIN_NAME below
PLUGIN_NAME=FlashGrab

# Copy recursively (-r) all modified files and folders, except the excluded ones
# (Like Anki's own deployment, this does NOT remove any files. The simplest way to do so manually here is to delete the addons folder, then re-run.)

# Use XDG_DATA_HOME if present, otherwise default to ~/.local/share
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
PLUGIN_HOME="${DATA_HOME}/Anki2/addons21/${PLUGIN_NAME}"

mkdir -p "${PLUGIN_HOME}"
rsync -r -u -v --exclude-from ExcludedFilesLinux.txt xml "${PLUGIN_HOME}/"
rsync -r -u -v --exclude-from ExcludedFilesLinux.txt xpath "${PLUGIN_HOME}/"
# No -r for syncxml since we don't want to include docsrc or samples directories
rsync -u -v --exclude-from ExcludedFilesLinux.txt syncxml "${PLUGIN_HOME}/"
# We do want one file from samples, but it should be in a top-level "samples" folder in the addons directory
mkdir -p "${PLUGIN_HOME}/samples"
rsync -u -v --exclude-from ExcludedFilesLinux.txt syncxml/samples/lift-dictionary.apkg "${PLUGIN_HOME}/samples/"
cp -u -v __init__.py "${PLUGIN_HOME}/"
cp -u -v manifest.json "${PLUGIN_HOME}/"
# Default config should also be in plugin root
cp -u -v syncxml/SyncFromXML_config_default.txt "${PLUGIN_HOME}/"
