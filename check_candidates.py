def name_match(osm, wd):
    wd_lc = wd.lower()
    osm_lc = osm.lower()
    if wd_lc == osm_lc:
        return True
    rs = ' railway station'
    if wd_lc.endswith(rs) and wd_lc[:-len(rs)] == osm_lc:
        return True
    comma = wd_lc.rfind(', ')
    if comma != -1 and wd_lc[:comma] == osm_lc:
        return True
    return False


for line in open('candidates'):
    wikidata, osm = eval(line)
    wd_name = wikidata['name']
    maybe = [(i['id'], i['tags']['name']) for i in osm
             if name_match(i['tags']['name'], wd_name)]
    if maybe:
        print (wikidata['id'], wd_name, maybe)
