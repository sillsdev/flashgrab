'''
This file does the GUI stuff, and syncxml.py does the work.
I don't have a full rig set up for 'compiling' PyQt and Anki, so I only debug some non-GUI behavior,
by using local_launch instead. For debugging within Anki itself, try Ctrl+Shift+; as shown here:
http://ankisrs.net/docs/addons.html#debugging 

@author: Jonathan Coombs, copyright sil.org 2012-2014
'''

# Force Python 3 syntax
from __future__ import print_function, absolute_import, division  , unicode_literals
import os
import shutil

from . import logg as L
from . import syncxml as SX
from . import anki_util as A
from . import xml_util as X
from . import flex_util as F

# 'Constants'
CFGMSG = "Sync from XML is not yet configured. You can do so from the Tools menu, or by manually creating a custom config file.\n"
IMPMSG = "Please do NOT use Import for data you wish to sync. Instead, sync from the Tools menu.\n"
TEST_PATH = "C:\\Users\\user57\\Documents\\dict4anki 2\\cgg.lift"  # what to use for testing if nothing else is found
TEST_FWDATA = ""  # making this non-empty makes the non-UI test run answer Yes and pick this as the FLEx project

if A.IN_ANKI:
    from aqt import mw
    from aqt.qt import *
    from aqt.utils import showInfo, askUserDialog, getFile
    from anki.notes import Note
    # from anki.utils import isMac  #obsolete now, I think
    # from PyQt4.QtGui import QMessageBox  #done for us already?
    QUESTION = QMessageBox.Question
    CRITICAL = QMessageBox.Critical
else:
    # crash-prevention dummies
    QUESTION = 0
    CRITICAL = 0

def msgbox(m):
    text = '{}: \n\n{}'.format(SX.ADDON_NAME2, m)
    L.debug("\n_____ Messagebox _____\n" + text + "\n----------")
    if A.IN_ANKI:
        no_hourglass()
        showInfo(text)

def dialogbox(text, buttons, icon=4, log=True):
    if log:
        L.debug("\n_____ Dialog _____\n" + text + "\n----------")
    if A.IN_ANKI:    
        no_hourglass()
        b = askUserDialog(text, buttons)
        if icon: b.setIcon(icon)
        x = b.run()
    else:
        x = buttons[0]  # first button is default when testing
    return x

def hourglass():
    if A.IN_ANKI:
        mw.app.setOverrideCursor(QCursor(Qt.WaitCursor))  # display an hourglass cursor
def no_hourglass():
    if A.IN_ANKI:
        mw.app.restoreOverrideCursor()
    

def try_sync(cfpath=SX.CONFIG_FILE):
    L.debug('Preparing to launch sync...')
    L.debug("Using config file: {}".format(cfpath))
    mm = ''
    if A.IN_ANKI:
        L.debug('===== Launching sync from within Anki... =====')
        hourglass()
        mm = SX.sync(cfpath)
    else:
        L.debug('===== Launching sync locally... =====')
        (all_src_records, num_src) = SX.sync(cfpath)
        e = L.error_count()
        w = L.warn_count()
        mm = 'errors: {}; warnings: {}'.format(e, w)
        mm += '\nDone reading from source file ({} records). That is all we can do for now (cannot access Anki from here), so quitting here.'.format(num_src)

    msgbox(mm)
    #  TODO: Prompt to auto-delete now-superfluous records. Check...
    #    mmm = """The target deck in Anki ({}) has existing data and/or media files in it. Delete or leave these?"""
    #    x = dialogbox(mmm, ['Yes', 'No', 'Cancel'], QUESTION)
    #    if (x == 'Cancel'): return


def on_sync_clicked():
    if A.IN_ANKI: A.anki_user_profile = mw.pm.profileFolder()    
    L.init(SX.LOG_FP, L.VERBOSITY)
    try:
        cfpath = SX.get_config_path() 
        if not os.path.exists(cfpath):
            # must create config before syncing
            L.w("Can't sync yet. Launching wizard to create the necessary config file: {}".format(cfpath))
            if wizard():
                try_sync()
        else:
            # A standard config file already exists. Sync.
            try_sync()
    finally:
        no_hourglass()
        launch_paths_maybe()
        # L.close_file() # Otherwise, you can't read the log until you've close Anki's error window.
    
    
def on_reconfigure_clicked():
    A.anki_user_profile = mw.pm.profileFolder()    
    L.init(SX.LOG_FP, L.VERBOSITY)
    try:
        if reconfigure():
            try_sync()
        else:
            L.w("Reconfiguration cancelled.")
            # msgbox("Reconfiguration cancelled.", close_log=True);
    finally:
        no_hourglass()
        launch_paths_maybe()
        # L.close_file()

def reconfigure(target=""):
    """Tries to reconfigure. Returns True if a sync should follow immediately."""
    L.debug('Preparing to reconfigure...')
    cfmainpath = SX.get_config_path()
    cfnewpath = SX.rename_config_to()
    if cfnewpath:
        msg = "Your existing configuration will be renamed to {}; Continue?".format(cfnewpath)
        x = dialogbox(msg, ['Ok', 'Cancel'], CRITICAL)
        if (x == 'Cancel'): 
            return False
        os.rename(cfmainpath, cfnewpath)
    result = wizard(target)
    return result

def ensure_models(models):
    """If we're in Anki and the given models (i.e. note types) don't all exist,
    create them by importing the sample APKG file, then deleting all
    records in the resulting deck. 
    ASSUMPTION: the sample APKG contains all needed models.
    WARNING: this could blow away user data in one unlikely scenario: user creates a lift_dictionary deck
    manually, or imports the APKG, and then manually enters data."""
    def all_models_ok(ms):
        for m in ms:
            if (not A.anki_model_exists(m)):
                L.w("Target data model '{}' does not yet exist. Will attempt to get it by importing the default APKG file.".format(m))
                return False
        return True
    
    if A.IN_ANKI:
        if not all_models_ok(models):
            no_hourglass()
            try:
                # Import the APKG.
                fp = A.get_filepath(A.APKG_PATH)
                delete_failure = A.import_apkg_model(fp, True)
                L.w("Done importing APKG file.")
                mw.col.models.flush()
                mw.reset(True)
                mw.reset()
                if delete_failure:
                    L.warn(delete_failure)  # not a big deal
                    msgbox(delete_failure)
                else:
                    L.w("Successfully deleted existing records.")
            except Exception as e:
                # We were unable to automatically import the APKG
                L.error(e)
                L.warn(A.NO_MODEL_MSG)
                msgbox(A.NO_MODEL_MSG + "\nError message: {}".format(e))
                return False
            return all_models_ok(models)  # verify
    return True


def wizard(target=""):
    """Assumption: The main config file does not exist. Auto-configure. 
    Returns True if successful and ready to sync.
    target: this parameter is for testing; it overrides the logic for finding a LIFT file."""
    L.debug('Launching the auto-config wizard')

    cfmainpath = SX.get_config_path()
    cfdefpath = SX.get_config_path(SX.CONFIG_DEFAULT_FILE)

    if not os.path.exists(cfdefpath):  # if no default config exists either...
        msg = "Cannot find and copy the default config file:\n  {}\nCannot continue.".format(cfdefpath)
        x = dialogbox(msg, ['ok'], CRITICAL)
        return False
    
    src_dir = SX.get_home_dir_plus(os.path.join(SX.get_docs_dir_name(), SX.SRC_DIR_LIFT), False)  # use True if creating dict4anki

    flex_dir = F.flex_dir()
    flex_msg = ''
    if flex_dir:
        flex_msg = "  For quickest results, give it the same name as one of the projects here:\n  {}\n".format(flex_dir)

     
    msg = "Would you like to bring in your own* LIFT data? If so, either...\n" \
    "A) FLEx users, export a LIFT file here (or to a direct subfolder of it):\n" \
    "  {} \n{}" \
    "B) WeSay (or FLEx) users can just click LIFT and choose a LIFT file.\n\n" \
    "A copy of the default configuration file will be auto-configured for you,\n" \
    "  which may take a few seconds. After configuration, the LIFT file to be synced\n" \
    "  must always be located in that same place.\n\n" \
    "Or, click Sample to sync from the sample file instead.\n\n" \
    "*Audio will only be auto-detected if your main writing systems are 2- or 3-letter codes."
    msg = msg.format(src_dir, flex_msg)
    # L.debug("Dialog: {}\n".format(msg))
    x = dialogbox(msg, ['LIFT', 'Sample', 'Cancel'], QUESTION)
    if (x == 'Cancel'): return False

    hourglass()
    
    # Make sure Anki has the default deck and models already there; else import the APKG file.
    if not ensure_models([X.MODEL1, X.MODEL2]):
        return False
    if (x == 'Sample'):
        # TODO idea: preprocess = (('vern', 'klw'),('other', 'id')) , hard-coding here.
        # After that, the default config file wouldn't need to be hard-coded to specific languages anymore.
        # Note that klw should cover klw-Zxxx-x-audio too, etc.
        try:
            msg = SX.sync(SX.CONFIG_DEFAULT_FILE)  # , preprocess)
            msgbox(msg)
            # launch_paths_maybe()
            return False
        except:
            # launch_paths(suppressExceptions=True)
            raise
        finally:       
            no_hourglass()

    hourglass()

    # prepare to copy default config to make a new config (via a temp file first)
    shutil.copy(cfdefpath, cfmainpath + '.tmp')  # will overwrite silently if need be
    
    lift = ''  # was: lift = SX.get_first_lift_file(src_dir) # check the dict4anki folder
    if not lift:  # fall back to anything in a direct subfolder of Documents\WeSay (Linux: ~/WeSay)
        tmp = SX.get_home_dir_plus(os.path.join(SX.get_docs_dir_name(), SX.SRC_DIR_WESAY))
        lift = SX.get_first_lift_file(tmp)
    if not lift:  # fall back to anything in a direct subfolder of Documents (Windows: %USERPROFILE%\My Documents; Linux: ~/)
        # src_dir = os.path.split(src_dir)[0]  # remove "/dict4anki/"
        lift = SX.get_first_lift_file(SX.get_home_dir_plus(SX.get_docs_dir_name()))
    if lift:
        src_dir = os.path.split(lift)[0]
    if A.IN_ANKI:
        no_hourglass()
        # pop up a File Open dialog using ankilib's convenience method
        lift = getFile(mw, "Open LIFT file", None, filter="*.lift", dir=src_dir, key="")  # "*.lift"
        L.debug("User chose this LIFT file: {}".format(lift))
    elif (not lift) and os.path.exists(TEST_PATH): 
        lift = TEST_PATH  # hard-coded test
    if target:
        lift = target  # for testing, a passed parameter overrides all of the above

    L.debug("Using this LIFT file: {}".format(lift))
    if not lift:   
        # Still no LIFT file. Fail.
        msg = "No file chosen. Auto-configuration cancelled for now." 
        x = dialogbox(msg, ['ok'], CRITICAL)
        return False
    
    m = "LIFT file: \n  {}\n".format(lift)
    flex_audio, flex_image = None, None

    # Check for WeSay. E.g. if Catalan.lift has a Catalan.WeSayConfig next to it, assume it's a WeSay project
    # Would it be better to make sure it's in the official WeSay directory?
    p, f = os.path.split(lift)
    f = os.path.splitext(f)[0]
    is_wesay = os.path.exists(os.path.join (p, f + ".WeSayConfig"))  

    if (not is_wesay) and flex_dir:
        L.debug("Checking for projects in this flex_dir: {}".format(flex_dir))
        tmp = F.flex_media(lift, flex_dir)
        L.debug("Found tmp: {}".format(tmp))
        if tmp: 
            flex_audio, flex_image = tmp

    if flex_audio:
        msg = "{}Also found a FLEx project with the same name as your LIFT file and it probably has these media folders:\n" \
          "  {}\n  {}\n" \
          "Shall we sync media files directly from there, so that before each \n" \
          "sync the only thing you'll have to export from FLEx will be the LIFT data?\n" \
          "(If No, the 'audio' and 'pictures' folders in the LIFT file's location will be used.)".format(m, flex_audio, flex_image)
        answer = dialogbox(msg, ['Yes', 'No'], QUESTION)
        if not A.IN_ANKI:
            # answer = 'No'  #Or, put the No button first, then delete this
            pass
        if answer != 'Yes':
            flex_audio, flex_image = None, None  # dump them
    elif not is_wesay:
        msg = "{}Could not find a FLEx project with the same name as your LIFT file.\n" \
          "Do you wish to select a FLEx project that does/will contain your media files? \n" \
          "WeSay users: choose No. FLEx users: choose Yes unless you want to export \n" \
          " the media files along with the LIFT before each sync.".format(m)
        answer = dialogbox(msg, ['Yes', 'No', 'Cancel'], QUESTION)
        if (answer == 'Cancel'): return False
        fwdata = TEST_FWDATA
        if (answer == 'Yes') and (A.IN_ANKI):
            # pop up a File Open dialog using ankilib's convenience method
            fwdata = getFile(mw, "Select FLEx project", None, filter="*.fwdata", key="", dir=flex_dir)
        if fwdata:
            tmp = F.flex_media(fwdata)
            if tmp: flex_audio, flex_image = tmp
        
    # Note: working with a temp copy of config, so as to not create an official config until we're sure we've succeeded.
    try:        
        xset = X.XmlSettings(cfmainpath + '.tmp', lift, flex_audio, flex_image)
    except:
        launch_paths(suppressExceptions=True)
        raise

    if os.path.getsize(lift) > 1000000:
        msg = m + "Your file is large, so analyzing it may take a while. Please click Ok and then wait."
        answer = dialogbox(msg, ['Ok', 'Cancel'], QUESTION)
        if answer == 'Cancel' : return

    # status bar (no longer supported by Anki?)
#    from aqt.main import setStatus as set_status
#    mw.setStatus("Analyzing the LIFT file...", timeout=3000)  

    # Find and Replace WS's in the new config file
    hourglass()
    to_replace = xset.find_vern_nat()
    L.w("For LIFT file\n  ({}) we will now find/replace writing systems in our settings as follows: \n{}".format(lift, X.lang_table(to_replace)))

    # Using regex (on cfmainpath + '.tmp') to replace WSes in our new config file ...
    xset.save() 
    tmp = xset.file_path
    X.replace_all(tmp, to_replace)
    xset = None  # since it is now outdated 
    # TODO: xset.dispose() # this would help with safety if implemented

    # do a dry run: use the new config file to load the LIFT file...
    try:
        xset = X.XmlSettings(tmp, lift, flex_audio, flex_image)  # we need those last two parameters or we'll lose any FLEx path we had
    except:
        launch_paths(suppressExceptions=True)
        raise
        
    xdl = X.XmlDataLoader()  # No try block, since presumably the user knows where the data file is.
    _recs, empties = xdl.load_src_file(xset.get_attr(), xset.entry, sync_media=False, dry_run=True)
    _recs, empties2 = xdl.load_src_file(xset.get_attr(), xset.example, sync_media=False, dry_run=True)
    # empties.append(empties2)

    # ... so we can disable any xpaths that don't match any data.
    if empties:
        L.w("The following entry fields yielded no data and will now be disabled so as to not generate warnings: {}".format(empties))
        xset.entry.disable_fields(empties)
    if empties2:
        L.w("The following example fields yielded no data and will now be disabled so as to not generate warnings: {}".format(empties))
        xset.example.disable_fields(empties2)

    # If no example sentences, we already disabled auto-disabled that section.
    if xset.example.get_attr()['enabled'] == 'true':
        # It's still enabled, which means it has data. 
        msg = m + "Found dictionary Examples containing data; when imported, each will show up on the main entry's flashcard.\n" \
              "Will you also need a separate flashcard for each Example?"
        x = dialogbox(msg, ['No', 'Yes', 'Cancel'], QUESTION)
        if (x == "Cancel"):
            return False
        if (x != 'Yes'): 
            xset.example.disable()

    hourglass()
    xset.save()

    # rename the default config file (remove the .tmp)
    shutil.move(cfmainpath + '.tmp', cfmainpath)  # will overwrite silently if need be, but see our initial assumption
    L.debug("Configuration file saved.")
    m2 = "\nReplaced writing systems in our new configuration as follows: \n{}".format(X.lang_table(to_replace))
    m3, m5 = '', ''
    if flex_audio:
        m3 = "\nConfigured to copy media files from these locations: \n  {}\n  {}\n".format(flex_audio, flex_image)
    m4 = "\nConfiguration file saved. Click Yes to sync now, or No if you wish to review/tweak the configuration first.\n"
    if L.error_count() or L.warn_count():
        m5 = "\nThere were errors or warnings during auto-config. Please review the log."
    msg = m + m2 + m3 + m4 + m5
    # TODO: " or want to run a Sync Preview."
    L.w(msg)
    # msgbox(msg)
    x = dialogbox(msg, ['Yes', 'No'], QUESTION)
    if (x == 'No'): 
        return False  # successful config, but don't sync right now
    return True
    
def launch_paths(suppressExceptions=False):
    """ Open the addon folder (ignoring any errors), 
    and open the log file (not ignoring errors, unless suppress).
    Typically called when there's a problem, to show the user where to go fix it.
    """

    tmp = os.path.abspath(os.curdir)
    folder = os.path.split(SX.LOG_FP)[0]
    try:
        launch_file(folder)  # Launch the folder containing the log file
    except: 
        pass  # ignore
    
    try:
        L.close_file()
        launch_file(SX.LOG_FP)  # Launch the log file (e.g. in Notepad)
    except:
        if not suppress:
            raise
    
def launch_paths_maybe():
    """ If there are errors/warnings, open the addon folder and the log file. """
    if L.error_count() or L.warn_count():
        launch_paths()
    else:
        L.close_file()

def launch_file(filepath):
    """See: http://stackoverflow.com/questions/434597/open-document-with-default-application-in-python
    Also note this alternative. Quote:
      I tried this code and it worked fine in Windows 7 and Ubuntu Natty:
      import webbrowser
      webbrowser.open("path_to_file")
    """
    if SX.WINDOWS:
        os.startfile(filepath)
    elif SX.MAC:
        import subprocess
        subprocess.call(('open', filepath))
    elif SX.LINUX:
        import subprocess
        subprocess.call(('xdg-open', filepath))  

if A.IN_ANKI:
    # create a new menu item in Anki
    action = QAction(SX.ADDON_NAME, mw)
    # set it to call our function when it's clicked
    mw.connect(action, SIGNAL("triggered()"), on_sync_clicked)
    # and add it to the tools menu
    mw.form.menuTools.addAction(action)
    
    action = QAction('(Re)configure ' + SX.ADDON_SHORT_NAME, mw)
    mw.connect(action, SIGNAL("triggered()"), on_reconfigure_clicked)
    mw.form.menuTools.addAction(action)

cpath = SX.get_config_path()
if A.IN_ANKI and (not os.path.exists(cpath)):
    showInfo(CFGMSG + "\n" + IMPMSG)

# TODO: have the config file indicate whether to sync automatically whenever Anki starts (e.g. for WeSay)
# But, there's a problem: mw.col is None at this point in Anki's loading process, so we 
# need a different way to get the collection object if we have to get it NOW. 
