To 'build' this addon, first make sure that the version number in syncxml.py is correct. Then, make a zip file containing these folders and this file:
syncxml/
distutils/
xml/
xpath/
syncx.py

Then, log in and upload the zip file to this addon's page: 
https://ankiweb.net/shared/info/915685712

Optionally, first make sure that the files here are up to date:
  syncxml/samples

That is, if you've edited the FLEx project, do this:
- Re-export that (with media) to LIFT
- If necessary, delete the Anki project, and Note Types DICT_LIFT/DICT_LIFT_EX, and reload this afresh:
  syncxml/samples/lift-dictionary.apkg
- Sync the LIFT/media into that fresh Anki deck, then re-create an updated .apkg file.
  At this point you could also re-share the .apkg file on its own, here:
  https://ankiweb.net/shared/decks/

