How to export a subset of entries from FLEx to LIFT for use in Anki,
or to export all and then limit in Anki.
 
How to use only a subset of entries from FLEx in Anki

(A) Type a code that you can filter on (e.g. "DIFC01") into an entry-level field in FLEx. Then, every time you want to sync your data to Anki, you would filter on this and export the filtered lexicon to LIFT. The best approach would be to add a custom list and list field (e.g. "Difficulty") to the entry level and use it to assign difficulty levels to each vocabulary item. You could then export just level 1 to Anki at first, then gradually add and export higher difficulty words over time.

(a1 - faster sync) A filtered export like this runs faster and keeps all your editing in FLEx. But it requires that you apply this same filter each time you export.

(a2 - less work for the human) export the whole lexicon every time, including that field. In Anki, enable/disable cards based on the field value. (The next sync will *not* blow away Anki's own info such as this disabling.)

Here is some help on filtering and suspending in Anki:
http://ankisrs.net/docs/dev/manual.html#searching
http://ankisrs.net/docs/dev/manual.html#editmore

There's also a new "filtered deck" feature that might provide exactly this functionality, but I have not yet tried it out:
http://ankisrs.net/docs/dev/manual.html#filtered

