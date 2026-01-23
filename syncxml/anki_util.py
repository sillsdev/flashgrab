'''
Code for interacting with Anki. If running locally (outside Anki), 
very little will work, though it does fall back to local folders a bit.  
'''

#Force Python 3 syntax

import os, sys

try:
    from aqt import mw
    IN_ANKI = True
    #anki_user_profile = mw.pm.profileFolder()  #can't do this yet; mw is still null
    from anki.importing import AnkiPackageImporter
except ImportError:
    IN_ANKI = False
anki_user_profile = '../User 1'  #'D:\\files\\user57\\documents\\Anki\\User 1'

ANKI_MEDIA_FOLDER = 'collection.media'

ADDON_FOLDER = 'FlashGrab'
APKG_PATH = os.path.join("samples", "lift-dictionary.apkg")
NO_MODEL_INSTR = "\nSteps: Restart Anki and make sure the target deck exists. Use Tools, Manage Note Types, or go to File Import, and import Anki/addons/{}/{}. Or, reconfigure.)".format(ADDON_FOLDER, APKG_PATH)
NO_MODEL_MSG = "The target model with the fields we needed was missing; have attempted to re-import the default APKG but an error occurred. \nPlease try again, or create it manually. \n{}".format(NO_MODEL_INSTR)
TARGET_DECK = "lift-dictionary"

def anki_model_exists(model):
    if (mw.col.models.byName(model)):
        return True
    return False



def addons_folder():
    fld = ".."
    if IN_ANKI:
        fld = mw.pm.addonFolder()
    return fld

def get_filepath(f):
    return os.path.join(addons_folder(), ADDON_FOLDER, f)



def get_anki_fields(modelname):  #(targ, source):
    """Given a model name, return a list/set of its fields."""

    n = ['Lexeme Form',
 'Citation Form',
 'Lex GUID',
 'Lex Audio',
 'Grammatical Info',
 'Glosses',
 'Definitions',
 'Reversals',
 'Picture',
 'Example',
 'Example Audio',
 'Example Translation',
 'xRxeversalxs']
    if not IN_ANKI:
        return n  #return hard-coded value
    
    model = mw.col.models
    mdict = model.byName(modelname)
    n = [x['name'] for x in mdict['flds']]
    return n

def add_field(key, modelname):
    model = mw.col.models
    mdict = model.byName(modelname)
    model.setCurrent(mdict) 
    f = model.newField(key)
    #mw.col.models.flush()
    model.addField(mdict, f) 
    model.save()   

def import_apkg_model(path, delete=False):
    #If delete==True, our sole purpose is to import the note types and flashcard templates, not the data.
    
    imp = AnkiPackageImporter(mw.col, path)
    imp.run()
    mw.col.models.flush()
    mw.reset(True) # refresh the screen so that the newly imported deck is visible

    if delete:
        # Delete ALL cards/notes in the LIFT deck. Ignore errors
        try:
#            deck = mw.col.decks.byName(TARGET_DECK)  #hmm, this returns a Python dict(); how to get the deck object?
#            assert deck.cardCount() > 0
#            assert deck.noteCount() > 0
            ids = mw.col.findCards("deck:{}".format(TARGET_DECK))
            mw.col.remCards(ids, True)
#            assert deck.cardCount() == 0
#            assert deck.noteCount() == 0
        except:
            return "Failed to delete cards and notes after importing the APKG file."
    
    mw.col.models.flush()
    mw.reset(True)
    return ""
