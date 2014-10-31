This module was copied unmodified from py-dom-xpath, which I downloaded here:
http://py-dom-xpath.googlecode.com/

It has a bug that prevents it from properly handling XML nodes named <text>, which is crucial for LIFT files.

This should be fixed, but for now a workaround is to make a temp copy that uses <texxt> instead, 
and run XPaths against that.
