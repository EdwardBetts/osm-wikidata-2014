import codecs
import cgi


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
    for f in 'candidates', 'candidates2':
        for line in open(f):
            wikidata, osm = eval(line)
            wd_name = wikidata['name']
            maybe = [i for i in osm if name_match(i['tags']['name'], wd_name)]
            if maybe:
                yield (wikidata, maybe)


def tag_table(osm):
    ret = u'<table>\n'
    for k, v in osm[u'tags'].items():
        if k.lower().startswith(u'name'):
            continue
        ret += u'<tr><td>{}</td><td>{}</td></tr>\n'.format(cgi.escape(k), cgi.escape(v))
    ret += u'</table>\n'
    return ret


def as_table():
    out = codecs.open('matches.html', 'w', 'utf-8')
    matches = list(find_matches())
    print >> out, u'<html><head>'
    print >> out, u'<title>Wikidata to OSM matches</title>'
    print >> out, u'<style>th { text-align: left; }</style>'
    print >> out, u'</head>'
    print >> out, u'<body>'
    print >> out, u'Found {:,} possible matches'.format(len(matches))
    print >> out, u'<table>'
    print >> out, u'<tr><th style="text-align:right">Wikidata</th><th></th><th>OpenStreetMap</th></tr>'
    for wikidata, osm in matches:
        print >> out, u'<tr>'
        print >> out, u'<td align="right" nowrap="nowrap"><a href="https://www.wikidata.org/wiki/{}">{}</a></td><td>{}</td>'.format(
              wikidata['id'], wikidata['name'], wikidata['id'])
        osm0 = osm[0]
        print >> out, u'<td nowrap="nowrap"><a href="http://www.openstreetmap.org/way/{}">{}</a> ({})</td>'.format(osm0['id'], osm0['tags']['name'], osm0['id'])
        print >> out, u'</tr>'
        if len(osm) > 1:
            for i in osm[1:]:
                print >> out, u'<tr><td></td><td></td>'
                print >> out, u'<td nowrap="nowrap"><a href="http://www.openstreetmap.org/way/{}">{}</a> ({})</td>'.format(i['id'], i['tags']['name'], i['id'])
                print >> out, u'</tr>'
    print >> out, u'</table></body></html>'

as_table()
