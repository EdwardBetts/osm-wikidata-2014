import codecs


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

def find_matches():
    for line in open('candidates'):
        wikidata, osm = eval(line)
        wd_name = wikidata['name']
        maybe = [(i['id'], i['tags']['name']) for i in osm
                 if name_match(i['tags']['name'], wd_name)]
        if maybe:
            yield (wikidata, maybe)

def as_table():
    out = codecs.open('matches.html', 'w', 'utf-8')
    print >> out, u'<html><head>'
    print >> out, u'<title>Wikidata to OSM matches</title>'
    print >> out, u'<style>th { text-align: left; }</style>'
    print >> out, u'</head>'
    print >> out, u'<body>'
    print >> out, u'<table>'
    print >> out, u'<tr><th>Wikidata</th><th>OpenStreetMap</th></tr>'
    for wikidata, osm in find_matches():
        print >> out, u'<tr>'
        print >> out, u'<td><a href="https://www.wikidata.org/wiki/{}">{}</a> ({})</td>'.format(
              wikidata['id'], wikidata['name'], wikidata['id'])
        osm0 = osm[0]
        print >> out, u'<td><a href="http://www.openstreetmap.org/way/{}">{}</a> ({})</td>'.format(
              osm0[0], osm0[1], osm0[0])
        print >> out, u'</tr>'
        if len(osm) > 1:
            for i in osm[1:]:
                print >> out, u'<tr><td></td>'
                print >> out, u'<td><a href="http://www.openstreetmap.org/way/{}">{}</a> ({})</td>'.format(
                      i[0], i[1], i[0])
                print >> out, u'</tr>'
    print >> out, u'</table></body></html>'

as_table()
