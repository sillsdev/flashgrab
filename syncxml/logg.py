'''
A simple logger.

@author: Jonathan Coombs, copyright sil.org 2012-2014
'''

#Force Python 3 syntax

import os
import platform

VERBOSITY_SILENT = 0
VERBOSITY_MINIMAL = 1
VERBOSITY_NORMAL = 2
VERBOSITY_DEBUG = 3
VERBOSITY = VERBOSITY_DEBUG  # Normally, choose VERBOSITY_NORMAL or VERBOSITY_DEBUG; VERBOSITY_SILENT might possibly help with unicode-related crashes.

# It's ok if client wants to set these differently, but remember it's a singleton
LOG_PATH = ''
LOG_FILE = 'logg.txt'

__MAIN_LOG = None # Mimics a singleton by using the following module-level methods 
    # Note that singletons aren't great, but ok for logging: http://googletesting.blogspot.com/2008/08/root-cause-of-singletons.html"""
    # Formerly I was doing something similar to this singleton: http://code.activestate.com/recipes/102263-logfilepy-a-singleton-log-file-creator/

def close_file():
    ''' Call this before telling the user to check the log, so they can see it all.
    This releases the log file without blowing away its object's error count, etc.
    You cannot then write to the log again without first doing a reset() or init().'''
    if __MAIN_LOG:
        __MAIN_LOG.close_file()

def init(fp=os.path.join(LOG_PATH, LOG_FILE), v=VERBOSITY):
    '''Must be called before you can start logging.'''
    global __MAIN_LOG
    close_file()
    __MAIN_LOG = Lg(fp, v)

def reset():
    init(__MAIN_LOG.path, __MAIN_LOG.verbosity)
       
#def close():  #Not needed? Just do init?
#    """Basically de-instantiates the singleton (in case the user might run the calling code again in the same session)"""
#    release()
#    __MAIN_LOG = None

def get_main_log(): return __MAIN_LOG

# convenience methods:
def error(msg): __MAIN_LOG.error(msg)
def warn(msg): __MAIN_LOG.warn(msg)
def w(msg): __MAIN_LOG.w(msg)
def debug(msg): __MAIN_LOG.debug(msg)
def error_count(): return __MAIN_LOG.error_count()
def warn_count(): return __MAIN_LOG.warn_count()


class Lg:
    '''A log class that both prints to stdout and writes to a log file.
    This is not a singleton, so it could be used, say, for a secondary log.'''

    def __init__(self,fp=os.path.join(LOG_PATH, LOG_FILE), v=VERBOSITY):
        self.path = fp
        self.verbosity = v
        self._num_errors, self._num_warnings = 0, 0

        self.f = open(fp, 'w+b') #will silently overwrite the log file
        self._w('Logging (verbosity level {}). Python interpreter is version {}.'.format(v, platform.python_version()))
        self._w('You are encouraged to search this log for "MSG:" labels to review errors and warnings.')
        self._w('This log is *overwritten* each time the addon runs, unless you make a copy.\n')

    def _w(self, msg, label = ''):
        ''' Write to the log. (Rewrite this method if we ever upgrade to Python 3.) '''
        s = '{}{}\n'.format(label, msg)
        out = s.encode('utf-8')  # don't crash the file output!
        self.f.write(out)
        s = s.encode('ASCII', 'replace')  # don't crash the console!
        print(s)

    def w(self, msg, label=''):
        if self.verbosity >= VERBOSITY_NORMAL:
            self._w(msg, label)

    def debug(self, msg):
        if self.verbosity >= VERBOSITY_DEBUG:
            self._w(msg)

    def warn(self, msg):
        self._num_warnings += 1
        if self.verbosity > VERBOSITY_SILENT:
            self._w(msg, 'WARNING MSG: ')

    def error(self, msg):
        self._num_errors += 1
        if self.verbosity > VERBOSITY_SILENT:
            self._w(msg, 'ERROR MSG: ')

    def close_file(self):
        if self.f:
            self.f.close()

    def error_count(self): return self._num_errors

    def warn_count(self): return self._num_warnings

