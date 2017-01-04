'''
Does most of the work of reading from XML and comparing it with what is in Anki.
Does not do any GUI interactions, so some of it would be unit-testable, but not the 
  parts that depend on the imports from Anki libraries: aqt and anki
Does not initialize or close the main log either; the calling code needs to do so.

@author: Jonathan Coombs, copyright sil.org 2012-2014
'''

#Force Python 3 syntax
from __future__ import print_function, absolute_import, division  , unicode_literals
from . import logg as L
from . import xml_util as X
from . import anki_util as A
import sys, os
#import glob  #is done below, FYI


try:
    from aqt import mw
    from anki.notes import Note
    IN_ANKI = True
    print("Successfully imported Python libraries from Anki.")
except ImportError:
    IN_ANKI = False
    sys.stderr.write("WARNING: Unable to import Python libraries from Anki. Assuming that this is just a local test run (outside of Anki).\n")

#TODO: ?? should these be repackaged so as to not conflict if another installed addon has bundled something with the same name? 
import os # , re, copy
from pprint import pformat as pformat


VERSION = 'v0.8.8'
ADDON_SHORT_NAME = 'FlashGrab'
ADDON_NAME = 'FlashGrab: one-way sync from XML'
ADDON_NAME2 = ADDON_NAME + ' ' + VERSION


# Filenames based on the following still need to get .txt appended to them
CONFIG_FILE = 'SyncFromXML_config'
CONFIG_DEFAULT_FILE = 'SyncFromXML_config_default'

SRC_DIR_WESAY = "WeSay"
SRC_DIR_LIFT = ""  # was "dict4anki" but that has become unhelpful (using the File Open dialog to choose is better)
""" TARGET_DECK = "DICT_LIFT"  # Make sure this matches the default config file! 
"""

MAC = False
WINDOWS = False
LINUX = False
if sys.platform.startswith('darwin'):  #Mac OS
    MAC = True
elif os.name == 'nt':  #Windows
    WINDOWS = True
elif os.name == 'posix':  #Linux
    LINUX = True  

HR = '=======================================================\n'
TAG_DELETE_ME = 'sfxDel'
#MEDIA_SUFFIX = '_srcpath'

LOG_FP = 'SyncFromXML_log.txt'
    
LOG_FP = A.get_filepath(LOG_FP) # os.path.join(A.addons_folder(), A.ADDON_FOLDER, LOG_FP)


def get_config_path(config_file=CONFIG_FILE):
    return A.get_filepath(config_file + '.txt') # os.path.join(A.addons_folder(), A.ADDON_FOLDER, config_file + '.txt')                

def get_new_name(cf):
    ''' Keep appending Bs to the filename until we get one that doesn't already exist. '''
    while (True):
        cf = cf + 'B'
        cfpath = get_config_path(cf)
        if (not os.path.exists(cfpath)): break  # might be SyncFromXML_configBBB.txt or something
    return cf

def rename_config_to():
    ''' If a config file exists, indicate what it should be renamed to. '''
    cfmain = CONFIG_FILE
    cfmainpath = get_config_path(cfmain)
    if os.path.exists(cfmainpath):  # if main config file already exists
        cfnew = get_new_name(cfmain)
        cfnewpath = get_config_path(cfnew)
        return cfnewpath
    return ''  # meaning: it doesn't exist (don't try to rename)

def get_home_dir_plus(mydir='', create=False):
    """"Get the user's home drive, make sure targetdir exists,
    then return the full path. """
    user = os.path.expanduser('~')
    targetdir = os.path.join(user, mydir)
    if mydir and not os.path.isdir(targetdir) and create:
        os.makedirs(targetdir)
    return targetdir
        

def get_docs_dir_name():

    user = os.path.expanduser('~')
    insert = '' # Linux: don't use a Documents folder even if it exists (since WeSay on Linux doesn't)
    if WINDOWS:
        insert = 'Documents' # Vista or newer
        if not os.path.exists(os.path.join(user, insert)):  
            insert = 'My Documents' # XP
    return insert
   
def get_first_lift_file(loc):
    """Returns a full path, or an empty string."""
    if not os.path.exists(loc): return ''
    from . import glob  #won't need to be done often
    mask = '*.lift'
    L.debug('Searching for {} in {} or its immediate subfolders'.format(mask, loc))
    pat = os.path.join(loc, mask)
    matches = glob.glob(pat)
    
    if not matches:
        # no match; check the immediate subfolders for the first match
        subd = os.listdir(loc)
        for s in subd:
            pat = os.path.join(loc, s, '*.lift')
            matches = glob.glob(pat)
            if matches: break

    if matches: 
        L.debug('LIFT file found in the following location:\n {}'.format(matches[0]))
        return matches[0]
    
    L.debug('No LIFT files found in {} or its immediate subfolders'.format(loc))
    return ''


def tostr(val):
    """Returns the supplied value as a string, but returns an empty string for false values like None. """
    r = ''
    if val: r = unicode(val)  #str(val)  #Python 2.x syntax  
    #TODO: see which other places need unicode(x). E.g. see the mix of str and unicode in the config attributes dict; not good
    return r


def fnote(n):
    """Takes an Anki note and returns a formatted string"""
    s = 'Anki Note:\n  items: {}\n  tags: {}'.format(pformat(n.items()), n.tags)
    return s

#def equivalent_time(t, t2):
#    return int(t) == int(t2)
#    return math.floor(t) == math.floor(t2)

def copy_to_anki(src, targ):
    """Copy the value of each source field into the corresponding target field.
    
    Ignore any extra fields in target.
    src is a Python dictionary
    targ is an Anki Note object
    """
    mod = []
    for key in src:
        v = tostr(src[key]).strip()
        v2 = tostr(targ[key]).strip()
        if v != v2:
            targ[key] = v
            mod.append(key)
    L.debug('COPIED FROM Source: {}'.format(src))
    L.debug('  TO Target: {}'.format(fnote(targ)))
    L.debug('  Fields affected: {}'.format(mod))
    targ.flush()

def add_to_anki(source, deck, model):
    n = Note(mw.col, model)  
    for key in source:
        tmp = tostr(source[key])
        try:
            n[str(key)] = tmp
        except KeyError:
            L.error("No {} field found in Anki. Try adding one to the model (the 'note type'), or deleting the model and reimporting the sample deck.".format(key))
    mw.col.addNote(n) #BUT, it will not be visible in Anki if no cards can be generated (i.e. if the fields needed by those cards are empty)
    n.flush()
    dm = mw.col.decks #get the DeckManager
    card_ids = [card.id for card in n.cards()] 
    #TODO: If the new note has no cards, just delete it now? Or at least give a warning that future syncs will keep adding invisible dups (unless the user adds the ID field to the front of a flashcard).
    dm.setDeck(card_ids, deck['id'])
    
    L.w('  ADDED to deck {}: {}'.format(deck['name'], fnote(n)))
    return n




def load_anki_records(combos):
    """For each combination key (deck, model), loads all matching Anki records.
    
    combos - a Python dictionary in which each key is a tuple, and each value is the name of an id field.
    Returns a dict in which the keys are tuples, and each value is a dict of all matching Anki records. 
    In this contained dict, the keys are specific IDs, and the values are Anki records. Each Anki record 
    is itself a dict of fieldname/value pairs.
    """
    
    all_anki_records = {}  # a dict of dicts of Anki notes
    models = set()  # for faster checking
    decks = set()
    for (deck_name, model_name) in combos:
        all_anki_records[(deck_name, model_name)] = {}
        models.add(model_name)
        decks.add(deck_name)

    L.w(HR)
    L.w('\nModels ("Note Types"): {}'.format(models))
    L.w('Decks: {}'.format(decks))
    L.w('Combos: {}\n'.format(pformat(combos)))

    for deck_name in decks:
        L.w('Loading deck {}...'.format(deck_name))
        #We can't find all notes for a given deck, so we find all cards and then get the cards' notes.
        #TODO: Change this so that invisible notes (notes with no cards and thus no decks) will still be found. Or, block the creation of invisible notes in the first place.
        card_ids = mw.col.findCards("deck:{}".format(deck_name))
        already_processed = set()
        for card_id in card_ids:
            note = mw.col.getCard(card_id).note()
            note_id = note.id
            if not note_id in already_processed:
                already_processed.add(note_id) #only process a note once (for its first card) 
                L.debug("\nLoading record, Anki note ID {}, deck {}.".format(note_id, deck_name))
#                note = mw.col.getNote(note_id)  #TODO: delete this line?
                model_name = note.model()['name']
#                L.debug("Anki record's model: {}".format(model_name))
                if model_name in models:
                    key = (deck_name, model_name)
                    if combos.has_key(key):
                        id_field = combos[key]
                        some_id = note[id_field].strip()
                        L.debug('\nFor ID {} loaded {}'.format(some_id, fnote(note)))
                        if not some_id:
                            L.warn('ID field is empty; IGNORING Anki record.')
                        elif all_anki_records[key].has_key(some_id):
                            L.warn('ID ({}) is not unique; IGNORING Anki record for now, but tagging it as {}.'.format(some_id, TAG_DELETE_ME))
                            note.addTag(TAG_DELETE_ME)
                        else:
                            all_anki_records[key][some_id] = note  # store this record
                            L.debug('Anki record loaded. ID is {}'.format(some_id))
                    else:
                        # This should no longer happen, since we're only looking within the specific deck now.
                        L.warn('Model (note type) matches but deck does not; IGNORING Anki record: {}'.format(fnote(note)))

    return all_anki_records

def equivalent(src, targ):
    """Compare the value of each source field against the corresponding target field. Iff all match, return True.
    Side effect: Add fields to the Anki model as needed.
    
    Ignore any extra fields in target.
    src is a Python dictionary
    targ is an Anki Note object
    """
    same = True
#   L.debug('Comparing.... Source: {}'.format(src))
#   L.debug('  Target: {}'.format(targ))
    for key in src:
        v = tostr(src[key]).strip()
        v2 = targ[key]
        v2 = tostr(v2).strip()  # might've raised a KeyError; shouldn't now
        if v != v2:
            same = False
            break
    return same

def guarantee_fields(sources):
    L.w("\nSeeing whether we need to add fields to Anki...")
    for source in sources:
        a = source.get_attr()
        modelname = a['anki_model']
        anki_fields = A.get_anki_fields(modelname)
        for f in source.get_fields():
            mydict = f.get_attr()
            key = mydict['anki_field']
            if not (key in anki_fields):
                L.error("Field {} did not yet exist in Anki. It's now being added, but it won't show on any flashcards. Try adding {{{{{}}}}} to a flashcard".format(key, key))
                A.add_field(key, modelname)
    

# This method probably could be refactored--rather big.
def sync(config_file=CONFIG_FILE):  #TODO: Add a "dry run" parameter
    """Performs a one-way sync, pulling data into Anki from the source XML file(s) as specified in the config file.
    
    Based on unique IDs, it compares the incoming records to any existing Anki records that match. If they differ 
    at all, the incoming source record is imported. Pseudocode below.
    
    Load all the XML source records into all_src_records
    Load all existing Anki records that are relevant into all_targ_records, a Python dictionary
    For each record in all_src_records:
        if no item with this record's ID exists in all_targ_records
            add a new note directly to Anki 
        else (there is a matching note):
            if it's different, update it
            if it's identical, don't
            remove any "superfluous" flag
            pop the item to delete it from all_targ_records
    For each item still remaining in all_targ_records:
        flag as "superfluous"
        if autodelete setting is True
            delete this Anki record (note that this won't affect records whose ID field is empty)
    NOTE: the ID referred to here is not the Anki ID, but rather a field in the source XML that the config 
    file claims will uniquely ID each record.
    """  

    config_path = get_config_path(config_file)
    setts = X.XmlSettings(config_path)
    settings = setts.get_attr()  #needs to be a dictionary of root attributes
    sources = setts.get_sources() #needs to be a list of XmlSource objects
    
    autodelete = settings['autodelete'] == 'true'
    syncmedia = settings['syncmedia'] == 'true'
    #TODO: maybe add a verbosity setting to config
    
    L.w("Addon's name is is {}".format(ADDON_NAME2))
    L.w('Done loading config file.\n')
    L.w('autodelete: {}; syncmedia: {}'.format(autodelete, syncmedia))
    if autodelete: raise Exception('Autodelete is not yet implemented.') 

    num_src, num_files_copied, num_targ = 0, 0, 0
    num_unchanged, num_added, num_updated, num_tagged, num_deleted = 0, 0, 0, 0, 0

    #load all specified XML source file(s)   
    xdl = X.XmlDataLoader()
    for source in sources:
        source_attribs = source.get_attr()
        enabled = source_attribs['enabled'].lower() == 'true'
#        source_fields = source.get_fields()
        if not enabled:
            continue        
        deck_name = source_attribs['anki_deck']
        model_name = source_attribs['anki_model']
        if IN_ANKI:
            model = mw.col.models.byName(model_name)
            deck = mw.col.decks.byName(deck_name)
            msg = ""
            if not deck:
                msg += "\nERROR. Aborted, because no deck named '{}' exists in Anki. \nIf you have renamed the target deck you can either change it back or edit the config file to match. Or, reconfigure.".format(deck_name)
            if not model:
                # This should now only happen if the user deletes/renames it, now that we have the earlier check (in the wizard) for anki_model_exists()
                msg += "\nERROR. Aborted, because model {} does not yet exist in Anki. \nPlease auto-reconfigure, or follow the configuration instructions in SyncFromXML_readme.txt.\n".format(model_name)
            if msg:
                msg += A.NO_MODEL_INSTR
                L.error(msg)
                return msg  #raise Exception(msg)
        L.w(HR)
        source_combo = "  {}\n  into deck {} using model {}".format(source_attribs['source_file'], deck_name, model_name)
        L.w("About to load from this source:\n  " + source_combo)

        _src_records, _empties = xdl.load_src_file(settings, source) #load one dict of records
        L.w("Done loading from this source:\n  " + source_combo)

    files_to_del = xdl.finish()   #was xdl.finish(settings['pathprefix'])
    if files_to_del:
        L.warn('\nThese files appear to be part of this dataset but are no longer referenced by it. Consider deleting them. (See also: Tools, Maintenance, Unused Media.) {}'.format(files_to_del))
        #TODO: implement autodelete? (or better, auto move to a folder named after our current timestamp)

    if not IN_ANKI: 
        return (xdl.all_src_records, xdl.num_src)
    #------------------------------------

    guarantee_fields(sources)
    all_src_records = xdl.all_src_records
    num_src = xdl.num_src

    #Load all existing Anki records that match any of our combo keys. Assume they all "belong to us".
    L.w("\nLoading existing Anki records...")
    all_targ_records = load_anki_records(xdl.combos)
    for key in all_targ_records: num_targ += len(all_targ_records[key])

    L.w("\nStarting the sync process...")
#    L.debug("  all_src_records ({} total) : {}".format(num_src, all_src_records))
#    L.debug("  all_targ_records ({} total) : {}".format(num_targ, all_targ_records))

    for (d, m) in all_src_records:
        deck = mw.col.decks.byName(d)
        model = mw.col.models.byName(m)
        combo = (d, m)
        L.w(HR)
        L.w('Importing data into deck {} (using model {}) as needed...'.format(d, m))
        for some_id in all_src_records[combo]:
            source = all_src_records[combo][some_id]
            L.debug('\nEvaluating source record : {}'.format(pformat(source)))
            if all_targ_records[combo].has_key(some_id):   # a record with this ID already exists
                target = all_targ_records[combo].pop(some_id) #pop the item to delete it from the Anki dict
                
                try:
                    L.debug("Comparing source {} and target {}...".format(source, target))
                    #target = A.add_fields(target, source)
                    if equivalent(source, target):
                        pass
                        L.debug('IS IDENTICAL to existing Anki record. Doing nothing. (ID is {})'.format(some_id))
                        num_unchanged += 1
                    else:
                        L.w('IS DIFFERENT from existing Anki record. Updating the fields that are pulled from the XML source file. (ID is {})'.format(some_id))
                        copy_to_anki(source, target)
                        num_updated += 1
                    target.delTag(TAG_DELETE_ME) #Remove any "delete me" tag, since we just checked/updated the record
                    target.flush()
                except KeyError as e:
                    L.error('CANNOT COMPARE these records. Check whether the Anki field names match up with the config files field names.\n  {}'.format(e))
            else:
                L.w('IS NEW. Adding a new record to Anki (model is {}). '.format(model['name']))
                add_to_anki(source, deck, model)
                num_added += 1

        L.w("\nDONE syncing deck + model: {} + {}\n".format(deck['name'], model['name']))

    L.w(HR)
#    L.w('About to autodelete or mark any remaining records as superfluous...')
    L.w('About to mark any remaining records as superfluous...')
#    L.w(all_targ_records)

    #Either tag for deletion or autodelete the remaining items. (Note that this won't affect records whose ID field is empty.) 
    for key in all_targ_records:
        for some_id in all_targ_records[key]:
            n = all_targ_records[key][some_id]
            if autodelete:
                raise Exception('Autodelete is not yet implemented.')
                L.warn('Deleting this note: '.format(fnote(n)))
#                mw.col.remNotes(some_id) #fails
                #TODO: implement autodelete
                num_deleted += 1
            else:
                n.addTag(TAG_DELETE_ME)
                n.flush()
                L.warn('Please search Anki for tag:{} and delete the matching items, including this one. You may want to first delete any media files. {}'.format(TAG_DELETE_ME, fnote(n)))
                num_tagged += 1
   
    msg = "Done syncing each combination of deck + model: {}.\n"
    msg += "Looked at {} XML source records, and at {} records already in Anki.\n"
    msg += "Summary of what was synced into Anki:\n  {} note(s) added,\n  {} updated,\n  {} tagged for manual deletion,\n  {} auto-deleted,\n  {} left unchanged.\n  {} media file(s) copied.\n"
    msg = msg.format(all_targ_records.keys(), num_src, num_targ, num_added, num_updated, num_tagged, num_deleted, num_unchanged, xdl.num_files_copied)
    msg += "{} error(s), {} warning(s).\n".format(L.error_count(), L.warn_count())
    msg += "To view your flashcard data, go to Browse and click your deck in the left pane.\n"
    # raise RuntimeError('PRETEND failure') # For verifying quick release of the log file
    L.w("\n" + msg)
    L.w('\nDone.')
    return msg

