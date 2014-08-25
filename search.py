from itertools import islice
import json
import os
import requests
from requests.adapters import HTTPAdapter
from math import pi, sin, cos, acos

s = requests.Session()
s.mount('http://overpass-api.de', HTTPAdapter(max_retries=10))

s2 = requests.Session()
s2.mount('https://www.wikidata.org', HTTPAdapter(max_retries=10))
s2.params = {
    'action': 'wbgetentities',
    'sites': 'enwiki',
    'format': 'json'
}


def get_lat_lon(i):
    if i['type'] == 'node':
        return i['lat'], i['lon']
    assert i['type'] == 'way'
    return i['center']['lat'], i['center']['lon']


def distance(lat1, lon1, lat2, lon2):
    "Find distance in m between two points."
    degrees_to_radians = pi / 180.0

    phi1 = (90.0 - lat1) * degrees_to_radians
    phi2 = (90.0 - lat2) * degrees_to_radians

    theta1 = lon1 * degrees_to_radians
    theta2 = lon2 * degrees_to_radians

    this_cos = (sin(phi1) * sin(phi2) * cos(theta1 - theta2) + cos(phi1) * cos(phi2))
    arc = acos(this_cos)

    earth_radius_km = 6371
    return arc * earth_radius_km * 1000


def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


def get_category_articles(cat, depth=4):
    url = 'http://tools.wmflabs.org/catscan2/catscan2.php'
    params = {'format': 'json', 'depth': depth, 'doit': 1, 'categories': cat}
    x = requests.get(url, params=params).json()

    for i in x['*'][0]['*']:
        title = i['a']['title']
        if title.startswith('List_of_'):
            continue
        yield title


def parse_wikidata(x):
    for q_id, entity in x['entities'].iteritems():
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


def buildings_from_overpass(items, tags, radius=400):
    filters = []
    for item in items:
        lat, lon = item['lat'], item['lon']
        for tag in tags:
            for t in 'node', 'way':
                filters.append('{}[{}]["name"](around:{},{},{});'.format(t, tag, radius, lat, lon))
    oql = '[timeout:360][out:json];({});\nout center;\n'.format(' '.join(filters))
    url = 'http://overpass-api.de/api/interpreter'
    r = s.get(url, params={'data': oql})
    try:
        json_data = json.loads(r.content)
    except ValueError:
        open('bad_overpass', 'w').write(r.content)
        raise
    return json_data['elements']


def get_data(cat, osm_tags):
    filename = 'found/' + cat + '.json'
    if os.path.exists(filename):
        print 'skipping', filename
        return
    titles = get_category_articles(cat)

    wikidata_url = 'https://www.wikidata.org/w/api.php'
    all_items = []
    for cur in chunk(titles, 10):
        r = s2.get(wikidata_url, params={'titles': '|'.join(cur)})
        content = r.content
        try:
            json_data = json.loads(content)
        except ValueError:
            open('bad_wikidata', 'w').write(content)
            raise
        items = list(parse_wikidata(json_data))
        found_osm = buildings_from_overpass(items, osm_tags)
        for item in items:
            distances = []
            for i in found_osm:
                try:
                    dist = distance(item['lat'], item['lon'], *get_lat_lon(i))
                except ValueError:
                    continue  # skip items with bad coords for now
                distances.append((dist, i))
            nearby = sorted((dist, i) for dist, i in distances if dist < 400)
            if not nearby:
                continue
            item['osm'] = sorted((dist, i) for dist, i in distances if dist < 400)
            all_items.append(item)

    json.dump(all_items, open(filename, 'w'), indent=2)

if __name__ == '__main__':
    for cats, osm_tags in json.load(open('entity_types')):
        for cat in cats:
            print (cat, osm_tags)
            get_data(cat, osm_tags)
