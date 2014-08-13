from itertools import islice
import requests
import codecs
import cgi
import json
import sys
from math import pi, sin, cos, acos

EARTH_RADIUS_KM = 6371 * 1000


def distance_on_unit_sphere(lat1, lon1, lat2, lon2):
    degrees_to_radians = pi / 180.0

    phi1 = (90.0 - lat1) * degrees_to_radians
    phi2 = (90.0 - lat2) * degrees_to_radians

    theta1 = lon1 * degrees_to_radians
    theta2 = lon2 * degrees_to_radians

    this_cos = (sin(phi1) * sin(phi2) * cos(theta1 - theta2) + cos(phi1) * cos(phi2))
    arc = acos(this_cos)

    return arc


def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


def show_tags(osm):
    interesting = {'tourism', 'railway', 'amenity', 'historic', 'railway',
                   'disused', 'craft', 'office', 'shop', 'leisure', 'aeroway',
                   'use', 'man_made'}
    return ' | '.join(u'{}={}'.format(k, cgi.escape(v))
                      for k, v in osm['tags'].items()
                      if k.startswith('name:') or k in interesting or k == 'building' and v.lower() != 'yes')


def parse_wikidata(x):
    for q_id, entity in x['entities'].items():
        if 'claims' not in entity:
            continue
        claims = entity['claims']
        if 'P625' not in claims:
            continue
        coords = claims['P625'][0]['mainsnak']['datavalue']['value']
        aliases = {lang: [i['value'] for i in value_list]
                   for lang, value_list in entity.get('aliases', {}).items()}
        labels = {lang: v['value'] for lang, v in entity['labels'].items()}
        yield {
            'labels': labels,
            'id': q_id,
            'lat': coords['latitude'],
            'lon': coords['longitude'],
            'aliases': aliases,
        }


def get_category_articles(cat, depth=3):
    url = 'http://tools.wmflabs.org/catscan2/catscan2.php'
    params = {'format': 'json', 'depth': depth, 'doit': 1, 'categories': cat}
    x = requests.get(url, params=params).json()

    for i in x['*'][0]['*']:
        title = i['a']['title']
        if title.startswith('List_of_'):
            continue
        yield title

s = requests.session()
s.params = {
    'action': 'wbgetentities',
    'sites': 'enwiki',
    'format': 'json'
}

# amenity=swimming_pool
# leisure=swimming_pool
# leisure=water_park


def buildings_from_overpass(item, tags, radius=100):
    print item['labels']['en']
    lat, lon = item['lat'], item['lon']
    node = ' '.join('node[{}]["name"](around:{},{},{});'.format(tag, radius, lat, lon) for tag in tags)
    way = ' '.join('way[{}]["name"](around:{},{},{});'.format(tag, radius, lat, lon) for tag in tags)
    oql = '[out:json];({}{});\nout center;\n'.format(node, way)
    url = 'http://overpass.osm.rambler.ru/cgi/interpreter'
    url = 'http://overpass-api.de/api/interpreter'
    print oql
    r = requests.get(url, params={'data': oql})
    #print r.url
    #sys.exit(0)

    return r.json()['elements']


def get_lat_lon(i):
    if i['type'] == 'node':
        return i['lat'], i['lon']
    else:
        return i['center']['lat'], i['center']['lon']


def make_web_page(filename, items):
    out = codecs.open(filename, 'w', 'utf-8')
    print >> out, u'<html><head>'
    print >> out, u'<meta charset="utf-8">'
    print >> out, u'<title>Wikidata to OSM</title>'
    print >> out, u'<style>th { text-align: left; } td { vertical-align: top;}</style>'
    print >> out, u'</head>'
    print >> out, u'<body>'
    print >> out, u'<table>'
    print >> out, u'<tr><th style="text-align:right">Wikidata</th><th></th><th>OpenStreetMap</th></tr>'
    for wikidata, osm in items:

        osm = sorted((distance_on_unit_sphere(wikidata['lat'], wikidata['lon'], *get_lat_lon(i)), i)
                     for i in osm)

        print >> out, u'<tr>'
        print >> out, u'<td align="right">'
        print >> out, u'<a href="https://www.wikidata.org/wiki/{}">{}</a>'.format(
              wikidata['id'], wikidata['labels']['en'])
        if wikidata['labels'].keys() > 1:
            print >> out, '<br>' + '; '.join(u'{}:{}'.format(lang, value) for lang, value in wikidata['labels'].items())
        print >> out, u'</td>'
        print >> out, u'<td>{}</td>'.format(wikidata['id'])
        # ?mlat=-85.051&mlon=45.862
        lat, lon = wikidata['lat'], wikidata['lon']
        print >> out, u'<td><a href="http://www.openstreetmap.org/?mlat={}&mlon={}#map=17/{}/{}">map</a></td>'.format(lat, lon, lat, lon)
        if osm:
            osm0 = osm[0][1]
            print >> out, u'<td nowrap="nowrap">{:.1f}m</td><td><a href="http://www.openstreetmap.org/{}/{}">{}</a> ({})</td><td>{}</td>'.format(osm[0][0] * EARTH_RADIUS_KM, osm0['type'], osm0['id'], osm0['tags']['name'], osm0['id'], show_tags(osm0))
        print >> out, u'</tr>'
        if len(osm) > 1:
            for dist, i in osm[1:]:
                print >> out, u'<tr><td></td><td></td><td></td>'
                print >> out, u'<td nowrap="nowrap">{:.1f}m</td><td><a href="http://www.openstreetmap.org/{}/{}">{}</a> ({})</td><td>{}</td>'.format(dist * EARTH_RADIUS_KM, i['type'], i['id'], i['tags']['name'], i['id'], show_tags(i))
                print >> out, u'</tr>'
    print >> out, u'</table></body></html>'

cat = 'Cinemas and movie theaters by country'
tags = ('amenity=cinema',)
filename = 'cinema.html'

cat = 'Brewery buildings'
tags = ('craft=brewery', 'building=brewery')
filename = 'brewery.html'

cat = 'Lighthouses by country'
tags = ('man_made=lighthouse',)
radius = 100
filename = 'lighthouse.html'

cat = 'Folly buildings'
tags = ('historic=folly',)
name = 'folly'

cat = 'Public houses by country'
tags = ('amenity=pub',)
radius = 100
name = 'pub'

cat = 'Swimming venues'
tags = ('amenity="swimming_pool"',
        'leisure="swimming_pool"',
        'leisure="water_park"',
        'leisure="stadium"',
        'leisure="lido"',
        'natural="water"')
name = 'swimming_pool'

cat = 'Windmills by country'
tags = ('man_made=windmill',)
name = 'windmill'

cat = 'Bus stations'
tags = ('amenity=bus_station',)
name = 'bus_station'


def get_data(cat, tags, name):
    titles = get_category_articles(cat)

    wikidata_url = 'http://www.wikidata.org/w/api.php'
    all_items = []
    for cur in chunk(titles, 20):
        r = s.get(wikidata_url, params={'titles': '|'.join(cur)})
        all_items += [(item, buildings_from_overpass(item, tags)) for item in parse_wikidata(r.json())]
    json.dump(all_items, open('cache/' + name + '.json', 'w'), indent=2)

get_data(cat, tags, name)
all_items = json.load(open('cache/' + name + '.json'))
make_web_page('output/' + name + '.html', all_items)
