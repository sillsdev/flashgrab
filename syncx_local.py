''' A test script. 
@author: Jonathan Coombs, copyright sil.org 2012-2014
'''

#Force Python 3 syntax
from __future__ import print_function, absolute_import, division  , unicode_literals


from syncxml import local_launch
from syncxml import xml_util as X
from syncxml import syncxml as SX
from syncxml import logg as L

import os

def get_path(name):
    f = SX.get_first_lift_file(os.path.join("..", "tests", name))
    return f

def get_lift_paths():
    L = os.listdir(os.path.join("..", "tests"))
    L2 = [get_path(x) for x in L]
    return L2
      


def count_ws():
    pass

def tests():
    """Some quick and dirty tests on auto-configuring and reading some actual LIFT files.
    Note: on my test machine, some of these have corresponding FLEx media folders, here:
    C:\ProgramData\SIL\FieldWorks\Projects\Bambara flashcards\LinkedFiles
    C:\ProgramData\SIL\FieldWorks\Projects\Moma-temp\LinkedFiles"""
    L.init(SX.LOG_FP, L.VERBOSITY_DEBUG)
    paths = get_lift_paths()
    #expected = dict()
    #expected['cgg'] =
    from time import sleep 
    for p in paths:
        """ WAS:
        # analyze the WSes in this file
        size = os.path.getsize(p)
        L.debug("File {} is {} bytes".format(p, size))
        lift_few = X.get_lift_subset(p, 30)  # .tmp
        langs = X.XmlLiftLangs(lift_few)
        v = langs.vern_ws
        n = langs.nat_ws
        os.remove(lift_few)
        """
        local_launch.main(p)
        sleep(0.5) # give Notepad a chance to open
    
    #count_ws()
    L.close_file()


if (__name__ == '__main__'):
    # If we're here, we're not running inside Anki, but we can still test/debug various pieces...
    os.chdir('syncxml') # go down one level, so we're in the same relative position as the Anki add-on

    tests()
    local_launch.main()
