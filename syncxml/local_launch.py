'''
A test module. Does some minimal loading. Outside of Anki, we can't do much, but we can at least parse the input file.
Needs to be imported from a script somewhere outside this package, and the osdir set to this one.
(See syncx_local .)

@author: Jonathan Coombs, copyright sil.org 2012-2014
'''

#Force Python 3 syntax


from . import syncxml as SX
from . import SyncFromXML as UI
from . import logg as L
import os
    
def main(target=""):
    ''' Runs a full set of tests on the non-Anki side of things. '''

    #If we're here, we're not running inside Anki, but we can still test/debug various pieces...
    L.init(SX.LOG_FP, L.VERBOSITY_DEBUG)
    L.debug('\nRUNNING LOCALLY!\n')

    try:
        # full test    
        if UI.reconfigure(target):
            cfpath = SX.get_config_path() 
            if not os.path.exists(cfpath):
                ##log error
                return
            
            ##L.debug('Reconfigure was successful.')  # So we know it's a success
            UI.try_sync()
            ##L.debug('Done--success.')  # So we know it's a success
        else:
            pass
            ##L.debug('Done--failed.')
    finally:
        UI.launch_paths_maybe()
        #L.close_file()
    
    