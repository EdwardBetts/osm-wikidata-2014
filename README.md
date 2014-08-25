osm-wikidata
============

This is a project to add wikidata tags to buildings on OSM.

The source file 'entity\_types.json' contains a list of records with three
fields. Each of the three fields is a list, they contain:

1. English Wikipedia category names,
2. OSM tags
3. Terms to strip from the start or end of a name when looking for a match

First run the 'search.py', for each record in entity\_types.json it will:

1. download a list of articles in that category and subcategories using
   Wikipedia CatScan
2. find matching wikidata items with geographical coordinates
3. use the OSM overpass API to find nearby OSM nodes and ways
4. saves candiate matches to a file on disk

Then run 'get\_matches.py', it will compare wikidata and OSM items to find
matching names.

Any wikidata item with multiple matching nearby OSM items is rejected.

Currently there are 82 cases where a given Wikidata item matches multiple OSM
items with different Wikipedia categories and OSM tags. For example there is a
bridge that appears as a single item Wikidata, in English Wikipedia it is
categorised as both a bridge and a monument. In OSM there is a way tagged as a
bridge and a node in the middle of the bridge tagged as a monument.
