osm-wikidata
============

This is a project to add wikidata tags to buildings on OSM.

First run the 'find\_candidates.py' tool, it will:

1. download a list of buildings using the Wikipedia CatScan tool
2. find matching wikidata items with geographical coordinates
3. use the OSM overpass API to find nearby OSM buildings
4. saves candiate matches to a file on disk

Then run 'check\_candidates.py', it will show wikidata and OSM buildings with matching names.

The next step is to check the candidates, then add wikidata tags to OSM.
