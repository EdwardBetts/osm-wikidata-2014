from itertools import islice
import json
import requests
import os


def read_coords(x):
    for q_id, entity in x['entities'].items():
        if 'claims' not in entity:
            continue
        claims = entity['claims']
        if 'P625' not in claims:
            continue
        coords = claims['P625'][0]['mainsnak']['datavalue']['value']
        yield {
            'name': entity['labels']['en']['value'],
            'id': q_id,
            'lat': coords['latitude'],
            'lon': coords['longitude'],
        }


def buildings_from_overpass(entity, delta=0.005):
    lat = entity['lat']
    lon = entity['lon']
    oql = ('[out:json];'
           'way["building"]["name"]({},{},{},{});'
           'out body;'
           ).format(lat - delta, lon - delta, lat + delta, lon + delta)

    url = 'http://overpass.osm.rambler.ru/cgi/interpreter'
    r = requests.get(url, params={'data': oql})

    return [w for w in (e for e in r.json()['elements'] if e['type'] == 'way')]


def get_buildings(x):
    titles = (i['a']['title'] for i in x['*'][0]['*'])
    wikidata_url = 'http://www.wikidata.org/w/api.php'
    total = len(x['*'][0]['*'])

    s = requests.session()
    s.params = {
        'action': 'wbgetentities',
        'sites': 'enwiki',
        'format': 'json'
    }

    def chunk(it, size):
        it = iter(it)
        return iter(lambda: tuple(islice(it, size)), ())

    num = 0
    for cur in chunk(titles, 20):
        num += len(cur)
        print 'done {} of {}'.format(num, total)
        r = s.get(wikidata_url, params={'titles': '|'.join(cur)})
        for i in read_coords(r.json()):
            yield i


def wikidata_and_osm(x):
    for entity in get_buildings(x):
        osm = buildings_from_overpass(entity, delta=0.005)
        if osm:
            yield (entity, osm)


def get_list_of_buildings(cat):
    filename = cat + '.json'  # cache
    if os.path.exists(filename):
        return json.load(open(filename))
    url = 'http://tools.wmflabs.org/catscan2/catscan2.php'
    params = {'format': 'json', 'depth': 3, 'doit': 1, 'categories': cat}
    r = requests.get(url, params=params)
    open(filename, 'w').write(r.content)
    return r.json()


def find_and_save_candidate_matches():
    out = open('candidates', 'w')
    cat = 'Buildings_and_structures_in_the_United_Kingdom'
    for entity, osm in wikidata_and_osm(get_list_of_buildings(cat)):
        print entity
        print >> out, (entity, osm)
        out.flush()
    out.close()

if __name__ == '__main__':
    find_and_save_candidate_matches()
