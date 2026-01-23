#Force Python 3 syntax

from . import logg as L
import os

FLEX_DIR = r"C:\ProgramData\SIL\FieldWorks\Projects"
FLEX_DIR_XP = r"C:\Documents and Settings\All Users\Application Data\SIL\FieldWorks\Projects"
FLEX_DIR_LINUX = r"~/.local/share/fieldworks/Projects"
LINKED_FILES = "LinkedFiles"
FLEX_AUDIO = "AudioVisual"
FLEX_IMAGE = "Pictures"

def flex_dir():
    d = ""
    tmp = os.path.expanduser(FLEX_DIR_LINUX)
    if os.path.exists(tmp):
        d = tmp
    elif os.path.exists(FLEX_DIR):  # Vista and later have priority
        d = FLEX_DIR
    elif os.path.exists(FLEX_DIR_XP):
        d = FLEX_DIR_XP
    return d

def flex_media(f, dir=""):
    """Given an absolute filepath such as c:\\files\\Catalan.lift, and the FLEx project folder,
    check whether audio and image folders are likely to be available under, say,
    C:\\ProgramData\\SIL\\FieldWorks\\Projects\\Catalan\\LinkedFiles
    Or, given just an absolute path, assume it's an fwdata file and deduce accordingly.
    """
    media_dir = ""
    if dir:
        base = os.path.split(f)[1] # e.g. just Catalan.lift
        proj = os.path.splitext(base)[0] # e.g. just Catalan
        media_dir = os.path.join(dir, proj, LINKED_FILES)
    else:
        # assume .fwdata
        dir, _f = os.path.split(f)
        media_dir = os.path.join(dir, LINKED_FILES)
        
    media_dir = os.path.normpath(media_dir) #fix any inconsistent slashes
    L.debug("Selected file is {}.\n  Checking to see if media_dir {} exists...".format(f, media_dir))
    if os.path.exists(media_dir):
        # Simply assume both of the following do or will exist
        au = os.path.join(media_dir, FLEX_AUDIO)
        im = os.path.join(media_dir, FLEX_IMAGE)
        L.debug("  It does. choosing {} and {}".format(au, im))
        return (au, im)
    else:
        L.debug("  It does not exist.")
    return None

