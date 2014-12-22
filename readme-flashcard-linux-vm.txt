This dev/test VM was created by Jonathan Coombs (SIL) in 2014.
- VM: created in Oracle VirtualBox (now using version 4.3.20 r96997
- Guest OS: Linux Mint 16 Mate 64-bit (basically Ubuntu 13.10)
- Host OS (shouldn't matter): Win7 Home Premium SP1 64-bit s
- Host MUST provide a folder mapped as "shared", which will show up in the VM as /media/sf_shared
  Recommended: keep that "shared" folder right next to the VM's .VDI file on the host machine
  Recommended: keep any source code repositories under "shared", so both OSes can access them. (E.g. you can do all your commit/pull/push actions from SourceTree on the Windows host.)

For more info on how/why this VM was set up, see the anki/README and anki/README.development files, which can also be found here:
  https://github.com/dae/anki
Basically, its easiest to imitate his Linux dev machine. If this help us learn how to *also* run (maybe even build) on the Windows host, that would be great too!
  
TO DO:
- each addon project still needs a shell script (like the Windows batch file, CopyFilesToAddons.bat) for copying changes into the addons folder (after every edit)

This VM can be used to...
...develop tweaks and addons for Anki. This is why Anki is NOT installed, although several packages it needs are. (See the Anki developer docs if you need to recreate this: )
  Rather, you should run Anki from source, which means that any tweaks you make will be reflected.
...test those tweaks/addons. In the case of FlashGrab, it helps to have a LIFT-producing app like FLEx. (Ideally, WeSay too, once a stable version can be pulled from the SIL repos.)
...test Fieldworks on Linux. (SIL repositories are already set up, and a version of FLEx installed.)

WARNING: Use Eclipse for editing text files under "shared". Pluma seems to be suffering from a glib bug where Linux text editors that use a temp file (like Pluma) have trouble saving edits properly to Windows SMB shares (although Save As still works):
  https://bugzilla.gnome.org/show_bug.cgi?id=656225
Eclipse (under either the host or guest) does not appear to suffer from this bug. (Not sure about nano, emacs, vim, etc.)

Our three projects (besides samples/tests) are:
1. flashgrab (addon)
2. flashgrid (addon)
3. anki (directly runnable; also referenced by both addons)
  
To run Anki, you can run it from the command line...
  adminuser@adminuser-VirtualBox / $ cd media/sf_shared/flashcards/anki/
  adminuser@adminuser-VirtualBox /media/sf_shared/flashcards/anki $ ./runanki
Or, in Eclipse, open the runanki file, right-click in it (or set perspective to PyDev and use the Run menu), and choose Run (Ctrl+F11) or Debug (F11). For debug, you'd want to first set a breakpoint somewhere in the *current* project. ( E.g. in the main anki project, you might set a breakpoint in main.py under setupAddons() or in addons.py under loadAddons(). )
  
Eclipse Workspaces ('Solutions') and Projects:
- A workspace in Eclipse is much like a solution in Visual Studio. Its info is stored as a hidden .metadata folder, such as:
  /media/sf_shared/flashcards/.metadata/
One workspace can contain multiple projects, which you might want to add to one 'working set' for easy global find/replace.
  Recommended: as in the current VM, include both addon projects and the anki project (and probably any related sample/test projects) in one "flashcards" workspace.
- If you ever have to recreate the workspace, you can delete the .metadata folder and import each project using File, Import, General, Existing...
- Similarly, an Eclipse project's info is stored in a hidden .settings folder, but it additionally includes a hidden project file and, for PyDev projects, a hidden pydevproject file.
  /media/sf_shared/flashcards/FlashGrab/.settings/
  /media/sf_shared/flashcards/FlashGrab/.project
  /media/sf_shared/flashcards/FlashGrab/.pydevproject
- To recreate a PyDev project, you can delete those and do File, New, Project, PyDev, PyDev. When choosing the Python interpreter, I'd choose "Python 2" as that should pick up the latest 2.x. Remember to recreate any cross-project references.
