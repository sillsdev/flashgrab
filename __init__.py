"""
Anki addon that performs a one-way sync, pulling data into Anki
from the source XML file(s) as specified in the config file.
"""

# Make package-local imports work in Python 3.6 and later
import os, sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from syncxml import SyncFromXML

