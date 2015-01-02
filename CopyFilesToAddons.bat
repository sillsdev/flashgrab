ECHO OFF
REM Windows script. Run this after editing the addon's files. Then restart Anki. 
REM Don't make edits over there in addons directly, as VCS won't see them, and an Anki or addon upgrade
REM might destroy them.
ECHO ON

REM copy all modified (D) files and folders (even E, empty ones), and overwrite (Y) without prompting
REM (Does NOT remove any files. The simplest way to do so manually is to delete the addons folder, then re-run.)

xcopy /D /E /Y /exclude:ExcludedFilesWindows.txt xml\*.* %USERPROFILE%\documents\Anki\addons\xml\
xcopy /D /E /Y /exclude:ExcludedFilesWindows.txt xpath\*.* %USERPROFILE%\documents\Anki\addons\xpath\
xcopy /D /E /Y /exclude:ExcludedFilesWindows.txt distutils\*.* %USERPROFILE%\documents\Anki\addons\distutils\
xcopy /D /E /Y /exclude:ExcludedFilesWindows.txt syncxml\*.* %USERPROFILE%\documents\Anki\addons\syncxml\
xcopy /D /Y syncx.py %USERPROFILE%\documents\Anki\addons\

PAUSE
