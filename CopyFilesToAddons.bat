ECHO OFF
REM A Windows 'build' script. Run this after editing the addon's files. Then restart Anki. 
REM Don't make edits over there in addons directly, as VCS won't see them, and an Anki or addon upgrade
REM might destroy them.

REM IMPORTANT: If you change the plugin package in manifest.json, make the same change to PLUGIN_NAME below
ECHO ON

SET PLUGIN_NAME=FlashGrab
SET ROOTFOLDER=%APPDATA%\Anki2\addons21\%PLUGIN_NAME%

REM copy all modified (D) files and folders (even E, empty ones), and overwrite (Y) without prompting
REM (Like Anki's own deployment, this does NOT remove any files. The simplest way to do so manually here is to delete the addons folder, then re-run.)

xcopy /D /E /Y /exclude:ExcludedFilesWindows.txt xml\*.* "%ROOTFOLDER%\xml\"
xcopy /D /E /Y /exclude:ExcludedFilesWindows.txt xpath\*.* "%ROOTFOLDER%\xpath\"
REM No /E for syncxml since we don't want to include docsrc or samples directories
xcopy /D /Y /exclude:ExcludedFilesWindows.txt syncxml\*.* "%ROOTFOLDER%\syncxml\"
REM We do want one file from samples, but it should be in a top-level "samples" folder in the addons directory
xcopy /D /E /Y /exclude:ExcludedFilesWindows.txt syncxml\samples\lift-dictionary.apkg "%ROOTFOLDER%\samples\"
xcopy /D /Y __init__.py "%ROOTFOLDER%\"
xcopy /D /Y manifest.json "%ROOTFOLDER%\"
xcopy /D /Y syncxml\SyncFromXML_config_default.txt "%ROOTFOLDER%\"

PAUSE
