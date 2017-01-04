''' Classes and functions for parsing XML files, both for config (read/write)
and data (read-only). 
ElementTree is convenient so
drops comments so I used minidom for the config file  
'''

#Force Python 3 syntax
from __future__ import print_function, absolute_import, division, unicode_literals

import xml.parsers.expat
#from xml.parsers.expat import ExpatError  # XML formatting errors
import xml.etree.ElementTree as ET #from Python 2.7.2
import xml.dom.minidom as MD #from Python 2.7.2
import xpath  #from http://py-dom-xpath.googlecode.com/
import os, re, copy, sys
import unicodedata
from . import anki_util as A
from . import logg as L
from pprint import pformat as pformat
from . import file_util

DEFAULT_NAT_LANG = 'en'
EXAMPLE = "Example"
MODEL1 = "LIFT_Word"
MODEL2 = "LIFT_Sentence"

# The vernacular and national WSes in the sample/default config file: 
VERN = 'klw'
NAT = 'id'
ENGLISH = "en"

class XmlError(Exception):
    pass


def normalize_path(s):                        
    # Also normalizing file paths, taking my cue from: https://github.com/dae/anki/blob/master/anki/media.py
    nf = 'NFC'  # Linux, Windows
    if sys.platform.startswith('darwin'):  # Mac OS
        nf = 'NFD'
    s = unicodedata.normalize(nf, s)
    return s   


def absolutize_addon(filename):
    """Returns an absolute version of the supplied file path. 
    
    Relative paths will be made absolute with this addon's folder as the base."""
    if not os.path.isabs(filename):
        relative = A.get_filepath(filename) # os.path.join(A.addons_folder(), A.ADDON_FOLDER, filename)
        L.debug("absolutize addon folder:  {} -->\n    {}".format(filename, relative))  # relative to our addon's folder
#        filename = relative
        filename = os.path.abspath(relative)
    return filename

def absolutize_media_folder(filename):
    """Returns an absolute version of the supplied file path. 
    
    Relative paths will be made absolute with the current Anki-user-profile folder as the base."""

    if not os.path.isabs(filename):
        L.debug("joining ({}) and ({}) and ({})".format(A.anki_user_profile, A.ANKI_MEDIA_FOLDER, filename))
        relative = os.path.join(A.anki_user_profile, A.ANKI_MEDIA_FOLDER, filename)
        L.debug("absolutize media path  {} -->\n    {}".format(filename, relative))
#        L.debug("Filename {} is not an absolute path; instead, we'll try it as relative to our user's profile folder: {}".format(filename, relative))
        filename = os.path.abspath(relative)
    return filename


def getAttributeDefault (elem, attrib, default):
    ''' A wannabe extension method. Returns the value if it exists; otherwise creates it with a default value.'''
    v = elem.getAttribute(attrib)
    if not v: 
        elem.setAttribute(attrib, default) # defaults to default if not already specified
        return default
    return v

def merge_dicts(d, d2):
    """Takes two dictionaries and merges the second into the first (possibly overwriting existing dups). Returns a list of overwritten dups."""
    bak = d.copy()
    d.update(d2)
    dup_count = (len(bak) + len(d2)) - len(d)
    dups = []
    if dup_count != 0:
        for key, val in bak.items():
            if d2.has_key(key):  #TODO: replace all dict.has_key(key) calls with the newer "key in dict" syntax
                dups.append((key, val))
    return dups

def _stringDict(d):
        d2 = {}
        for k in d.keys():
            d2.setdefault(k, d[k].value)
        return d2

class XmlSourceField(object):
    '''Represents a <source_field> element in the XML file.'''
    def __init__(self, elem):
        '''MD.Element expected.'''
        self.src = elem
        #The following properties won't be saved back into the config file
        self.data_count = 0
        self.xpath_massaged = ''  # This is a massage version of the xpath
    def __repr__(self):
        att = self.get_attr()
        return str(att)
    def get_attr(self):
        '''Returns a (read-only) copy of this element's attributes (or _ if it isn't an element),
        as a dictionary (string keys, string values).'''
        return _stringDict(self.src.attributes._attrs)
#    def get(self, key):
#        self.src._attrs.get(key).value

class XmlSource(object):
    '''Represents a <source> element in the XML file.'''
    def __init__(self, elem, parent):
        '''MD.Element expected.'''
        self.src = elem
        self._parent = parent
    def get_attr(self):
        '''Returns a (read-only) copy of this element's attributes (or _ if it isn't an element),
        as a dictionary (string keys, string values).'''
        return _stringDict(self.src.attributes._attrs)
    def get_fields(self):
        '''Returns a list of XmlSourceField.'''
        L = []
        for sf in self.src.childNodes:
            if (sf.nodeType != MD.Node.ELEMENT_NODE):
                continue
            L.append(XmlSourceField(sf))
        return L
    def disable(self):
        self.src.setAttribute('enabled', 'false')

    def disable_fields(self, to_disable):
        '''Given a list of xpaths, this disables the fields that contain them.'''
        L = self.get_fields()
        for f in L:
            x = f.src.getAttribute('xpath')
            if x in to_disable:
                f.src.setAttribute('enabled', 'false')  #call disable() instead?
                if f.src.getAttribute('anki_field') == EXAMPLE:
                    self._parent.disable_example()
       
        
#    def get_model(self):
#        return self.src.attributes._attrs['anki_model'].value

def get_lift_subset(file_path_orig, stop_after=50):
    ''' Return a copy of this LIFT file containing only N entries '''
    
    file_path = file_path_orig + ".tmp"
    root = None
    tree = ET.ElementTree ()
    
#    root = ET.Element('lift')
#    tree = ET.ElementTree (root)

    c = 0
    for event, elem in ET.iterparse(file_path_orig, events=("start",)):
        if elem.tag == "entry":
            root.append(elem)
            c += 1
            if (c >= stop_after):
                break
        elif elem.tag == "lift":
            tree._setroot(elem)
            root = tree.getroot()
        else:
            root.append(elem)

    tree.write(file_path, 'utf-8')
    return file_path

class XmlSettings(object):
    '''Represents a <sources> element in the XML file.'''

    def get_attr(self):
        return _stringDict(self.dom.documentElement.attributes._attrs)
    
    def get_sources(self):
        sources = []
        root = self.dom.documentElement
        for source in root.childNodes:
            if (source.nodeType != MD.Node.ELEMENT_NODE):
                continue
            sources.append(XmlSource(source, self))
        return sources

    def save(self, file_path=''):
        """Plain Save (without parameters) or Save As (with params)."""
        if not file_path:
            file_path = self.file_path
        bytes = self.dom.toxml('utf-8')
        with open (file_path, mode='w') as outfile:  # Python 3 would also allow: encoding='utf-8'
            outfile.write(bytes)

    def __init__(self, file_path, source_file='', source_audio=None, source_image=None):
        """Reads in the configuration (XML) file which maps the source XML file(s) to the Anki deck(s). 
        It only really stores the minidom, but it (and XmlSource) provide more convenient read access 
        via get methods that return string dictionaries.
        If the optional parameters are provided, they will overwrite whatever was in those
        attributes for *every* source element. If just source_file is provided, e.g. C:\mylift\Catalan.LIFT,
        then audio and image will be deduced, e.g. C:\mylift\audio and C:\mylift\pictures . 
        NOTE: if source_file is not provided, the other source_ parameters will be ignored.
        """
        
        #parse the document into a DOM tree
        # Error handling here is based on: http://stackoverflow.com/questions/192907/xml-parsing-elementtree-vs-sax-and-dom
        try:
            s = self.dom = MD.parse(file_path)  # may raise an error, if bad XML
        except xml.parsers.expat.ExpatError as e:
            msg = "The config file is not proper XML! Cannot continue.\n" + \
                  "Please fix the config file or the default config file.\n" + \
                  "[XML] Error (line {}): {}\n".format(e.lineno, e.code) + \
                  "[XML] Offset: {}".format(e.offset)
            L.error(msg)
            raise XmlError(msg)
        except IOError as e:
            msg = "[IO] I/O Error {}: {}".format(e.errno, e.strerror)
            L.error(msg)
            raise
        
        self.file_path = file_path
        self.entry, self.example = None, None #shortcuts to the two standard source elements

        L.debug("Loading XmlSettings file: source_file {}, source_audio {} , source_image {}".format(source_file, source_audio, source_image))
        if source_file:
            base, f = os.path.split(source_file)
            if source_audio == None:
                source_audio = os.path.join(base, 'audio')
            if source_image == None:
                source_image = os.path.join(base, 'pictures')  # Wesay's LIFT paths are stored inconsistently
            
        L.debug("source_image {}".format(source_image))

#        MD.parse().documentElement
        root = s.documentElement
        if (root.tagName != 'sources'):
            raise XmlError('The root element must be <sources>.')

        for source in root.childNodes:
            if (source.nodeType != MD.Node.ELEMENT_NODE):
                continue
            if (source.tagName != 'source'):
                raise XmlError('The children of <sources> must all be <source>.')
            getAttributeDefault(source, 'enabled', 'true')
            
            # Grab these in case we need auto-config
            if source.attributes._attrs['anki_model'].value == MODEL1:  # "DICT_LIFT"
                self.entry = XmlSource(source, self)
            if source.attributes._attrs['anki_model'].value == MODEL2: # "DICT_LIFT_EX"
                self.example = XmlSource(source, self)
            
            # Overwrite, if so specified by caller (for auto-config)
            if source_file:
                source.setAttribute('source_file', source_file)
                source.setAttribute('source_audio_folder', source_audio)
                source.setAttribute('source_image_folder', source_image)

            for sf in source.childNodes: #for each source_field element
                if (sf.nodeType != MD.Node.ELEMENT_NODE):
                    continue
                if (sf.tagName != 'source_field'):
                    raise XmlError('The children of <source> must all be <source_field>.')
                getAttributeDefault(sf, 'enabled', 'true')
                #guarantee that the following two settings always exist, and make them boolean (not string)
                is_audio, is_image = False, False
                aud = getAttributeDefault(sf, 'is_audio', 'false').lower()
                img = getAttributeDefault(sf, 'is_image', 'false').lower()
                if (aud == 'true') and (img == 'true'): 
                    raise Exception('A single field cannot be designated as both audio and image. Field: {}'.format(sf))

        return

    def disable(self):
        self.src.setAttribute('enabled', 'false')
    def disable_example(self):
        self.example.disable()
       
    def find_vern_nat(self):
        if not self.entry:
            raise Exception('Did not find a source for the {} model in the config file. Cannot auto-config.'.format(MODEL1))
        a = self.entry.get_attr()
        lift = a['source_file']
        lift_few = get_lift_subset(lift, 30)  # .tmp

        langs = XmlLiftLangs(lift_few)
        v = langs.vern_ws
        n = langs.nat_ws
        os.remove(lift_few)
                  
        if not v:
            raise Exception('No vernacular writing systems found! Cannot auto-configure.')

#        L.debug("Found writing systems. vern: {} nat: {}. Choosing vern={} and nat={} .".format(langs.vern_ws, langs.nat_ws, v, n))

        return (('{' + NAT + '\\b', '{AnalysisWs'), ('{' + VERN + '\\b', '{' + v), ('{AnalysisWs', '{' + n))  
        # E.g. this will replace {id-Zxxx-x-audio} with {fr-Zxxx-x-audio} while safely not
        # changing id_field to fr_field . (It could corrupt comments about curly {idioms} but that's rare enough. 
        # NOTE: The initial Temp replacement is to protect "id" in cases where Indonesian is the vernacular (and something else is the national).

        # TODO: improve find_vern_nat() wrt:
        # This will NOT work in tricky cases. E.g. if the core WS is "flh-x-Abawiri" rather
        # than "flh" then it will FAIL to change "klw-Zxxx-x-AUDIO" to "flh-Zxxx-x-AUDIO"


class XmlLiftLangs(object):


    def __init__(self, lift):
        '''Parse a LIFT source file into its core fields:
        typical vern / vern-aud : Citation Form, Lexeme Form, Example
        typical nat / nat-aud: Definition, Gloss, Translation
        typical en not needed? (Definition, Gloss, Translation)
        Pronunciation too?
        '''

        self.vern_ws = None
        self.nat_ws = DEFAULT_NAT_LANG

        self.xmlp = XmlParser(lift)
        vern = ['//entry/lexical-unit/form/@lang', '//entry/pronunciation/form/@lang', '//entry/sense/example/form/@lang']
        nat = ['//entry/sense/gloss/@lang', '//entry/sense/definition/form/@lang', '//entry/example/translation/form/@lang']
        L.debug("Counting occurrences of vern and nat WSes in {}".format(lift))
        v = self.xmlp.find_langs(vern)
        n = self.xmlp.find_langs(nat) 
        L.debug("Found and counted usages of writing systems.\n  vern: {} nat: {} ".format(v, n))
        if v:
            self.vern_ws = v[0][0]
        if n:
            self.nat_ws = n[0][0]
        else:
            self.nat_ws = ENGLISH

        L.debug("Decided vern={} and nat={} .".format(self.vern_ws, self.nat_ws))



class XmlParser(object):
    """Using minidom, parses the source XML file (e.g. LIFT) immediately 
    and provides its content via a couple of attributes. """
#    tree = None  #an rdf_tree
#    entries = []
#    context = None
    def __init__(self, filename, base_xpath="//entries"):
        #parse the document into a DOM tree
        # Error handling here is based on: http://stackoverflow.com/questions/192907/xml-parsing-elementtree-vs-sax-and-dom
        try:
            self.tree = rdf_tree = MD.parse(filename)
        except xml.parsers.expat.ExpatError as e:
            msg = "Error: The data file is not proper XML! Cannot continue." + \
                  "[XML] Error (line {}): {}\n".format(e.lineno, e.code) + \
                  "[XML] Offset: {}".format(e.offset)
            L.error(msg)
            raise XmlError(msg)
        except IOError as e:
            msg = "[IO] I/O Error {}: {}".format(e.errno, e.strerror)
            L.error(msg)
            raise
            
        #read the default namespace and prefix from the root node
        self.context = xpath.XPathContext(rdf_tree)
        self.entries = self.context.find(base_xpath, rdf_tree)
        

    def find_langs (self, xpaths, ignore_audio=True, ignore_en=False):  # used to default to ignore_en=True but that's not so helpful now that the count is more precise 
        ''' (Functionally static.)
        Given a list of xpaths representing lang= attributes, return a list giving 
        each WS that was found and a count of how many times. Sorted with highest numbers first.'''
        
        audio = '-Zxxx-x-audio'  
        main_codes = dict()
        root_codes_needed = set()
        
        tr = self.tree  #rdf_tree
                    
        for x in xpaths:
            try:
                values = self.context.findvalues(x, self.tree) 
            except xpath.exceptions.XPathParseError as e:
                L.error("Error that will prevent good autoconfig! Error in xpath: {}".format(x))
                continue
            value_set = set(values)
            #values = sorted(set(values), key=len) #gives audio WSes a very high chance of coming last in the list
            for val in value_set:
                core = val.split('-')[0]
                #core = re.sub(r'^([^-]+).*$', r'\1', val)  # would this be more reliable?
                if ignore_en and core.lower() == ENGLISH:
                    continue
                if ignore_audio and val.lower().endswith(audio.lower()):
                    root_codes_needed.add(core)  #ignore audio for now, but we'll need its core to cover it
                else:
                    c = main_codes.setdefault(val, 0) #get
                    main_codes[val] = c + values.count(val)

        problems = root_codes_needed.difference(set(main_codes.keys()))
        if problems: 
            msg = "Verify that each of the following audio input systems corresponds to a core writing system. \n" \
              "Example: id-Zxxx-x-audio would correspond to id. Without this, audio data will probably not sync \n" \
              "unless you edit the config file: {}".format(problems)
            L.warn(msg.format(val, core, val + audio, core + audio))
    
        s = main_codes.items()
        #Sort: highest count first; secondary sort prefers shorter WS names. E.g. ('flh', 1) beats ('flh-x-Lisan', 1) 
        s.sort(key=lambda x: x[1]*99 - len(x[0]), reverse=True) 
        return s
        

def lang_table(t):
    s = ''
    try:
        for row in t:
            s += "  Replaced lang={} with lang={}\n".format(row[0], row[1])
        return s
    except IndexError:
        return "  Replaced lang= " + str(t) + "\n"

def wesay_workaround(val):
    """Remove leading 'pictures\' from the beginning of this filename string.
    
    For some reason, WeSay puts this before pictures but nothing similar before audio.
    FLEx export to LIFT does neither."""
    
    val2 = re.sub(r'(pictures[/\\])?(.*)', r'\2', val)
    return val2
    

class XmlDataLoader:
    """This class mainly just contains a method for loading data, but it has some state."""
    
    def __init__(self):
        self._media_files = {} # a dictionary for checking uniqueness of the target path
        self._deck_names = set() # a set of deck names used for checking media files (for deletion) 
        self.media_files_to_delete = []
        self.num_files_copied = 0
        self.combos = {} # a dictionary for tracking each combination we've loaded from so far
        self.all_src_records = {}  # a dict of dicts of records
        self.num_src = 0 # the total number of source records (before any merging)
    #TODO: refactor load_src_file() and sync(); they've grown big and ugly

    def load_src_file(self, settings, source, sync_media=None, dry_run=False):
        """Loads data from one specified source file into memory; returns a dictionary of records, keyed on an id field.
        
        settings - a dictionary of settings that apply across all source files
        source - an XmlSource object
        source.source_attribs - a dictionary of attributes specifying a source file
        source.source_fields -  (a list of dictionaries; each dictionary contains all the attributes of a single field)
        SIDE EFFECT (if not dry_run): if sync_media, it copies media files into the target location. (Since the media files can 
          come from various folders but must end up in a single folder, uniqueness is verified before copying them.)
        Each item in the returned dictionary can be accessed via its id. Each item is itself a dictionary of 
        fields (key/value pairs for field-name/value). Thus, each source field will have one corresponding field 
        in the returned dictionary; however, fields that contain media file paths will result in two corresponding fields, 
        one containing the original media file's absolute path, and the other containing the relative path to copy it to.
        Note: uses py-dom-xpath to parse the XML data file (since that package supports XPath more fully).
        """ 
        source_attribs = source.get_attr()
        source_fields = source.get_fields()
        if sync_media == None:
            sync_media = settings['syncmedia'] == 'true'
        
        filename = absolutize_addon(source_attribs['source_file']) #filename may include some path bits too
        source_audio_folder = absolutize_addon(source_attribs['source_audio_folder'])
        source_image_folder = absolutize_addon(source_attribs['source_image_folder'])
        tmp = 'Loading from source file...\n  sync_media={} dry_run={}\n  filename: {}\n  source_audio_folder: {}\n  source_image_folder: {}'
        L.debug(tmp.format(sync_media, dry_run, filename, source_audio_folder, source_image_folder))
    
        # First, work around a py-dom-xpath bug by regex-replacing all <text\b and </text\b with <texxt and </texxt
        #   bug report: https://code.google.com/p/py-dom-xpath/issues/detail?id=8
        #   Alternative: maybe could've used the minidom API to rename those element nodes in memory after the initial parse.
        filename = filename_tmp = _workaround_px(filename)
    
        xmlp = XmlParser(filename, source_attribs['base_xpath'])
        deck_name = source_attribs['anki_deck']
        self._deck_names.add(deck_name)
        id_field = source_attribs['id_field']
    
        recs = {}
        num_files_copied = 0
        empties = []
        
        # Groundwork: for each field, add a massaged (tweaked) xpath and a 'data found' counter
        for sf in source_fields:
            sfa = sf.get_attr()
            path = sfa['xpath']
            path = re.sub(r'/text\b', r'/texxt', path) #workaround B for the py-dom-xpath bug
            path = re.sub(r'{(.+?)}', r'"\1"', path) #workaround for my (optional) alternative {ws} syntax, which avoids XML's &quot;ws&quot; syntax.
            #lastpart = path.rsplit('/', 1)[-1]
            #if not (u'@' in lastpart) or (u'[' in lastpart):
                    # target data is not an attribute, so it's safe to append the following (maybe it w/b safe anyway)
            sf.xpath_massaged = path  + '/descendant-or-self::text()'
#            #TODO: NEED TO TEST: does that extra part tacked onto the xpath really handle cases of embedded data/tags??
            sf.data_count = 0

        # Load the data
        errmsg = 'XPathParseError. So, field {} will not be loaded for this record. xpath: \n'
        for entry in xmlp.entries:
            rec = {}
            id = None
            L.debug('\n---------- loading record... ----------')
            for sf in source_fields:
                sfa = sf.get_attr()
                enabled = sfa['enabled'].lower() == 'true'
                if not enabled:
                    continue
                path = sf.xpath_massaged
    
                first_only = (sfa['grab'] == 'first')
                value, values = '', ['']
                if first_only:
                    try:
                        value = xmlp.context.findvalue(path, entry) # returns a string
                    except xpath.exceptions.XPathParseError:
                        L.error(errmsg.format(sfa['anki_field'], path))
                else:  # The config settings say there can be multiple values, to be smushed together.
                    try:
                        values = xmlp.context.findvalues(path, entry)  # returns a list of strings
                    except xpath.exceptions.XPathParseError:
                        L.error(errmsg.format(sfa['anki_field'], path)) 
                    value = settings['multivalue_separator'].join(values)
                #TODO: replace with a single try/except block
                
                if value:
                    value = value.strip() 
                    sf.data_count += 1
                else:
                    value = ''

#                L.debug('type(value): {}'.format(type(value)))
#                if value: value = value.decode('utf-8')
                    
                if (sfa['anki_field'] == id_field) and value:
                    if value in recs:
                        L.warn('ID is not unique. This source record will be IGNORED (ID is {})'.format(value))
                    else:
                        id = value
                
                is_audio, is_image = sfa['is_audio'] == 'true', sfa['is_image'] == 'true'
    
                if (is_audio or is_image) and value:
    
                    if is_audio:
                        source_path = source_audio_folder
                    else:
                        source_path = source_image_folder
                        value = wesay_workaround(value)
                    source_path = os.path.join(source_path, value)
    
                    # generate an extra 'field' to keep track of the source media file
                    abs_source_path = os.path.abspath(source_path)
    #                rec[sfa['anki_field'] + MEDIA_SUFFIX] = abs_source_path  #beware of side effects in add_to_anki()
    
                    target_path = ''
                    if sync_media:
                        target_path = os.path.split(source_path)[1] #filename only
                        target_path = deck_name + "_" + target_path #prefixed since Anki allows no subfolders; prefix helps with sorting and uniqueness, and identifying deletables
                        if self._media_files.has_key(target_path) and self._media_files[target_path] != abs_source_path:
                            L.error('A different source media file already resolved to this same target name ({}). Will not attempt to copy the file.'.format(target_path))
                        else:
                            self._media_files[target_path] = abs_source_path
                        abs_target_path = absolutize_media_folder(target_path)
                        abs_target_path = normalize_path(abs_target_path)
                        
                        if not os.path.exists(abs_source_path):  
                            # filename may be NFD in LIFT file but the OS filename is probably NFC; try NFC
                            abs_source_path = unicodedata.normalize('NFC', abs_source_path)
                        if not os.path.exists(abs_source_path):
                            # still no good; last try: just in case the OS file was NFD and not the LIFT
                            abs_source_path = unicodedata.normalize('NFD', abs_source_path) 

                        if os.path.exists(abs_source_path):
                            # We found the source file!
                            try:
                                src_time, target_time = os.path.getmtime(abs_source_path), os.path.getmtime(abs_target_path)
                            except os.error:
                                src_time, target_time = 2, 1  # need to copy the file
                            L.debug('comparing t {} and t2 {}'.format(src_time, target_time))
                            if int(src_time) == int(target_time): #round down to the nearest second
                                pass
                            elif src_time < target_time:
                                L.error('The target media file already exists and is newer: ({}). Will not attempt to copy the file.'.format(target_path))
                            elif not dry_run:
                                file_util.copy_file(abs_source_path, abs_target_path, update=0, dry_run=0)
                                num_files_copied += 1
                                L.debug("FILE COPIED from {} to {}".format(abs_source_path, abs_target_path))

                             # I wanted to use update=1 but it failed: it would always copy, except when the target file was newer. (on WinXP 32 bit)
                             # from the Python 3.2 docs: If update is true, src will only be copied if dst does not exist, or if dst does exist but is older than src. 
#                            (fname, copied) = distutils.file_util.copy_file(abs_source_path, abs_target_path, update=1, dry_run=0)
#                            if copied: num_files_copied += 1
                        else:
                            msg = 'Source media file {} does not exist. Cannot copy it.'.format(abs_source_path)
                            L.warn(msg)
    
                    else:
                        target_path = abs_source_path
    
                    if is_audio: 
                        value = '[sound:{}]'.format(target_path)
                    else: 
                        value = '<img src="{}"/>'.format(target_path)
    
                rec[sfa['anki_field']] = value
                
            #Done loading this entry's fields' data; store the data for later.
            if id:
                recs[id] = rec
                s = rec.get('Lexeme Form', '')
                s2 = pformat(rec)
                L.debug('Source record ({} , ID {}) loaded: {}'.format(s, id, s2))
            else:
                L.warn('No ID or non-unique ID; IGNORING this item:\n{}'.format(rec))

        L.debug('\n\nSummary for this source of records:')
        for sf in source_fields:
            sfa = sf.get_attr()
            if not sf.data_count and sfa['enabled'].lower() == 'true':
                msg = "Empty field: {}. The entire file appears to contain NO DATA for this field. That's fine during initial config; otherwise there's likely an error in the config file's xpath for this field.\n  DETAILS: {}".format(sfa['anki_field'], sfa)
                if dry_run:
                    L.debug(msg)
                else:
                    L.warn(msg)
                empties.append(sfa['xpath'])
            else:
                L.w("{} field: A total of {} record(s) in the file contained data for this field.".format(sfa['anki_field'], sf.data_count))
            
        os.remove(filename_tmp) #done with workaround A
        self.num_files_copied += num_files_copied 

        self.merge(recs, source_attribs)
        
        return recs, empties

    def merge(self, src_records, source_attribs):
        deck_name = source_attribs['anki_deck']
        model_name = source_attribs['anki_model']
        combo = (deck_name, model_name)
        id_field_name = source_attribs['id_field']
        self.combos[combo] = id_field_name
        if not self.all_src_records.has_key(combo):
            # This is our first time loading into this deck/model combination
            self.all_src_records[combo] = src_records
            self.num_src += len(src_records)
        else: 
            # Not our first time, so we may need to merge data from multiple sources
            L.w('Multiple sources specified for one exact destination ({}). Combining them into one set of source records.'.format(combo)) 
            dups = merge_dicts(self.all_src_records[combo], src_records)
            if dups:
                L.error('There were {} pair(s) of records that existed in both source files. The second was kept in each case, so the following records from the first were ignored:\n{}\n'.format(len(dups), dups))
            self.num_src += len(src_records) - len(dups)

        
    def finish(self):
        """Closes the loader now that we're finished loading from the XML file(s); returns a list of orphaned media files that begin with a deckname + _ ."""

#        media_files = set( [prefix + f for f in self._media_files.keys()] )
        media_files = set(self._media_files.keys())
        deck_names = self._deck_names
        self._media_files, self._deck_names = None, None  #reset
        delete_these = []
        L.debug("media_files: {}".format(media_files))
        
        base_path = absolutize_media_folder('')
        
        # Re-write the following if Anki ever starts supporting subfolders again.
        listing = os.listdir(base_path)
        sep = "_"
        for file in listing:
            if sep in file:
                prefix = file.split(sep)[0]
                if prefix in deck_names and (not file in media_files):
#                if file.startswith(prefix + "_") and (not file in media_files):  
                    delete_these.append(file)

        #OR: for file in glob.glob( os.path.join(base_path, prefix + '*') )  #nice wild-card search, but Anki doesn't provide glob 
        
        self.media_files_to_delete = delete_these
        return delete_these
    


def replace_all(fname, to_replace, target=None):
    '''Given a filepath and a list of regex replacement pairs, this will
    1. open the file for silent overwrite, 2. apply the changes, 3. silently save
    Assumption: it's okay to silently overwrite any file ending in .temp.tmp
    '''
    
    if not target:
        target = fname
    
    # the while loop below was safer, but too fancy since we sometimes crash and can't easily clean it up. Then too many .tmp.tmp.tmp files get generated.
#    fname2 = fname + ".tmp"
#    while os.path.exists(fname2):
#        fname2 += ".tmp"

    # using python 2.x decode()/encode() syntax below, since its open() function doesn't support this v3 parameter: encoding='utf-8'
    with open(fname, 'r') as infile:
        data = infile.read().decode('utf-8')
        for pair in to_replace:
            data = re.sub(pair[0], pair[1], data)
    with open (target, 'w') as outfile:
        outfile.write(data.encode('utf-8'))

def _workaround_px(fname):
    """Makes a copy of the source XML file, replacing all <text> elements with <textt>
    """

    to_replace = (("<text\\b", "<texxt"), ("</text\\b", "</texxt"))
    fname2 = fname + ".temp.tmp"
    replace_all(fname, to_replace, fname2)
    return fname2

