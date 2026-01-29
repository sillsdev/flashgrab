@ECHO OFF
REM A Windows 'build' script.
REM
REM If you modify this, make corresponding changes to BuildZip.sh

IF NOT EXIST "C:\Program Files/7-Zip/7z.exe" (
  ECHO This script uses 7-Zip to build the .zip file, but 7-Zip does not seem to be installed, so the script will fail.
  ECHO The script also assumes that 7-Zip is installed in its default location, C:\Program Files/7-Zip/7z.exe
  ECHO So please do not change the default install location of 7-zip when you install it.
  EXIT /B 1
)

REM Delete and recreate temporary folder so we don't end up copying old files
RMDIR /S /Q %TEMP%\FlashGrabBuild
MKDIR %TEMP%\FlashGrabBuild

REM Copy files into folder
xcopy /D /E /Y /exclude:ExcludedFilesWindows.txt xml\*.* %TEMP%\FlashGrabBuild\xml\
xcopy /D /E /Y /exclude:ExcludedFilesWindows.txt xpath\*.* %TEMP%\FlashGrabBuild\xpath\
REM No /E for syncxml since we don't want to include docsrc or samples directories
xcopy /D /Y /exclude:ExcludedFilesWindows.txt syncxml\*.* %TEMP%\FlashGrabBuild\syncxml\
REM We do want one file from samples, but it should be in a top-level folder in the zip file
xcopy /D /E /Y /exclude:ExcludedFilesWindows.txt syncxml\samples\lift-dictionary.apkg %TEMP%\FlashGrabBuild\samples\
REM The default config also needs to live in the top-level folder
move %TEMP%\FlashGrabBuild\syncxml\SyncFromXML_config_default.txt %TEMP%\FlashGrabBuild\
xcopy /D /Y /exclude:ExcludedFilesWindows.txt __init__.py %TEMP%\FlashGrabBuild\
xcopy /D /Y /exclude:ExcludedFilesWindows.txt manifest.json %TEMP%\FlashGrabBuild\

PUSHD %TEMP%\FlashGrabBuild
"C:\Program Files/7-Zip/7z.exe" a FlashGrab.zip syncxml samples xml xpath __init__.py manifest.json SyncFromXML_config_default.txt
POPD

MOVE %TEMP%\FlashGrabBuild\FlashGrab.zip .

ECHO FlashGrab.zip file created!
DIR FlashGrab.zip
PAUSE
