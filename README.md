FlashGrab (a.k.a. lexml2anki, SyncFromXml, syncxml)
==========

Please see https://github.com/sillsdev/flashgrab/wiki for an overview.

The "Sync one-way from XML" addon for Anki pulls data into Anki from one or more external XML sources, as 
determined by a config file. It does not modify fields that are specific to Anki (e.g. it does not reset any existing 
flashcards), but it WILL OVERWRITE any edits that you've made within Anki to the data that was pulled in. The 
assumption is that you want to do your editing elsewhere and simply pull the latest data into Anki.

Note: if you'll be importing LIFT data, the first thing the auto-config does is import the 
.apkg file. (It is located in the samples folder next to this readme file; that is, in 
%userprofile%\My Documents\Anki\addons\syncxml\samples .) This will put the needed structures in place so that 
there are enough fields in the Anki deck to receive several different dictionary fields. 

After that, the wizard will try to auto-configure itself for your LIFT data.

The rest of this readme file describes the details of the config file. For general documentation, see 
SyncFromXML_help.pdf instead. (You may find also find the log file useful for troubleshooting during the initial 
configuration.)

CONFIG DETAILS:

The configuration (SyncFromXML_config.txt) file tells the addon:
- where to find the XML file to pull its data from, 
- where precisely the data is located within that source file, and 
- where to store it in Anki. 

Before running the addon, try editing the config file by specifying the source file paths and carefully replacing the writing system codes between the &quot; or {} marks. Also make sure that the correct model / note type (e.g. DICT_LIFT) is available in Anki (the easiest way to do this is to import the preconfigured sample deck), and make sure that 'deckname' refers to the Anki deck you wish to copy your data into. This should be enough to start pulling data in from your LIFT file. 


CONFIGURATION OPTIONS:

source_file, source, source_field: To start pulling data into Anki, the source_file path needs to point to an XML file, and there needs to be a valid 'source' element containing at least one valid 'source_field' element. You can supply multiple source files if you wish, by specifying multiple 'source' elements. (And a single source file may be used more than once.)

To load from the addon's 'samples' subfolder, just a short relative path will suffice for each path. Example:

    source_file="samples/Lindu-Test.lift" 
    source_audio_folder="samples/audio"
    source_image_folder="samples/pictures" >

But assuming your own source file is located elsewhere, you'll want to specify absolute paths. Example:

    source_file="D:\files\user7\documents\LIFT-from-FLEx\Lindu-Test\Lindu-Test.lift" 
    source_audio_folder="D:\files\user7\documents\LIFT-from-FLEx\Lindu-Test\audio"
    source_image_folder="D:\files\user7\documents\LIFT-from-FLEx\Lindu-Test\pictures" >

audio_folder, image_folder: The base paths for finding any media files whose links are not already stored as absolute paths in the XML file.

base_xpath: The base_xpath for each source matches on the root element that will correspond to one Anki note, and all source_field elements must be relative to that base path, representing the fields that will be copied over into that note. For example, given a LIFT file as input, the <entry> element would typically be specified as the root, and each source_field would point to something within <entry>, such as Lexeme Form, Gloss, Illustration, etc.

grab: Typically, you should specify grab="first" for each field, in which case only the first matching value will be copied over. But for non-media fields, you may also specify grab="concat_all", in which case multiple values will be concatenated (separated by a separator such as ;;). In the sample config file, multiple glosses and multiple definitions are handled using concat_all.

autodelete: This should be set to "false" since this feature is not yet implemented.


ASSUMPTIONS AND LIMITATIONS: 
- Each sync operation will OVERWRITE the matching data in any matching Anki note. This is intentional, allowing you to do all of your editing externally rather than doing duplicate work in Anki.
- Currently, *all* matching records are imported from the source file. If you want a filtered subset, you'll need to trim down the XML file. (E.g. in FLEx, you can choose to filter down to a desired subset before exporting to LIFT XML.)


DEVELOPER NOTES:
- Standard XPath syntax is used in this config file, except that quotes need to be escaped, either using the standard &quot;ws&quot; syntax, or using my non-standard {ws} syntax. (The addon supports the latter for convenience/readability.)
- The XPath actually used by the sync software will consist of (a) the base_path, plus (b) the field's own xpath fragment, plus (c) descendant-or-self::text() .
- Anything involving links would be hard to pull in cleanly, since these are stored as (long) IDs in LIFT. XPath has no way of 
  knowing how to follow LIFT links. However, the first part of the ID is usually readable, so pulling the whole thing into 
  an Anki field might be barely usable, though ugly, as in this example for synonyms. Ditto for other links (e.g. confer).

    <source_field anki_field="Synonyms" xpath="sense/relation[@type={Synonyms}]/@ref" grab="concat_all" />

  A link to "absuwelto" would display like this: absuwelto_e50fee0e-45d3-43d3-bc71-b6cd4983607c
  
  Probably not worth it. And doing this for variants or complex forms specifically is even trickier, since distinguishing between 
  them would require looking deeper down first, into the nested <trait> element, to decide whether or not its parent is a match.
  
  - The XPath syntax supported by this addon is all standard, with one tweak: since these xpaths are embedded here 
  in XML elements, quotation marks should not be used directly. Rather than using &quot; every time, curly brackets are supported.

  - I think the following ought to work, but doesn't; the syntax for reading attributes instead of filtering on them 
  seems poorly supported (though it works for the root element's guid attribute):

    <source_field anki_field="Lex Audio" xpath="pronunciation/media@href" grab="first" />

