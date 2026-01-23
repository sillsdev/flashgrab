#!/usr/bin/env bash
# A Linux build script

which 7z || (
  echo 7zip not found. Please install the 7zip package, e.g. sudo apt install 7zip or sudo pacman -S 7zip
  exit 1
)

# Delete and recreate temporary folder so we don't end up copying old files
rm -rf /tmp/FlashGrabBuild
mkdir /tmp/FlashGrabBuild

# Copy files into folder
rsync -r -u -v --exclude-from ExcludedFilesLinux.txt xml /tmp/FlashGrabBuild
rsync -r -u -v --exclude-from ExcludedFilesLinux.txt xpath /tmp/FlashGrabBuild
rsync -r -u -v --exclude-from ExcludedFilesLinux.txt syncxml /tmp/FlashGrabBuild

cp -u -v __init__.py /tmp/FlashGrabBuild
cp -u -v manifest.json /tmp/FlashGrabBuild

# Some files under syncxml need to live in top-level directory
mv /tmp/FlashGrabBuild/syncxml/SyncFromXML_config_default.txt /tmp/FlashGrabBuild
mkdir -p /tmp/FlashGrabBuild/samples
mv /tmp/FlashGrabBuild/syncxml/samples/lift-dictionary.apkg /tmp/FlashGrabBuild/samples

# Rest of samples and docsrc from syncxml dir doesn't need to be in the addon, to save file size
rm -rf /tmp/FlashGrabBuild/syncxml/docsrc
rm -rf /tmp/FlashGrabBuild/syncxml/samples

pushd /tmp/FlashGrabBuild
7z a FlashGrab.zip syncxml samples xml xpath __init__.py manifest.json SyncFromXML_config_default.txt
popd

mv /tmp/FlashGrabBuild/FlashGrab.zip .
ls -l FlashGrab.zip
