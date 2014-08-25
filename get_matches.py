from collections import defaultdict
from copy import copy
import json
import os
import re
from unidecode import unidecode

re_strip_non_chars = re.compile('\W', re.U)

endings = {}
for cats, amenity, end in json.load(open('entity_types.json')):
    end = [x.replace(' ', '').lower() for x in end]
    for cat in cats:
        endings[cat.replace('_', ' ')] = end


def tidy_name(n):
    n = n.replace('saint ', 'st ')
    if n[-1] == 's':
        n = n[:-1]
    n = n.replace('s ', ' ').replace("s' ", '')
    for word in 'the', 'and', 'at', 'of', 'de', 'le', 'la', 'les':
        n = n.replace(' {} '.format(word), ' ')
    n = n.replace('center', 'centre').replace('theater', 'theatre')
    return unidecode(n)


def name_match(osm, wd, endings):
    wd_lc = wd.lower()
    osm_lc = osm.lower()
    if not wd or not osm:
        return False

    if re_strip_non_chars.sub('', wd_lc) == re_strip_non_chars.sub('', osm_lc):
        return True
    wd_lc = tidy_name(wd_lc)
    osm_lc = tidy_name(osm_lc)
    if not wd_lc or not osm_lc:
        return False
    if wd_lc == osm_lc:
        return True
    comma = wd_lc.rfind(', ')
    if comma != -1 and wd_lc[:comma] == osm_lc:
        return True
    if wd_lc.split() == list(reversed(osm_lc.split())):
        return True
    wd_lc = re_strip_non_chars.sub('', wd_lc)
    osm_lc = re_strip_non_chars.sub('', osm_lc)
    if wd_lc == osm_lc:
        return True
    if wd_lc.startswith('the'):
        wd_lc = wd_lc[3:]
    if osm_lc.startswith('the'):
        osm_lc = osm_lc[3:]
    if wd_lc == osm_lc:
        return True

    for end in endings:
        if wd_lc.endswith(end) and wd_lc[:-len(end)] == osm_lc:
            return True
        if wd_lc.startswith(end) and wd_lc[len(end):] == osm_lc:
            return True
        if osm_lc.endswith(end) and osm_lc[:-len(end)] == wd_lc:
            return True
        if osm_lc.startswith(end) and osm_lc[len(end):] == wd_lc:
            return True
    return False


def process():
    d = 'found'

    num = 0
    all_matches = defaultdict(set)
    wikidata_lookup = {}
    osm_lookup = {}
    for f in os.listdir(d):
        filename = os.path.join(d, f)
        print filename
        cat = f[:-5].replace('_', ' ')
        for item in json.load(open(filename)):
            all_aliases = []
            for i in item['aliases'].values():
                all_aliases += i
            wikidata_names = set(item['labels'].values() + all_aliases)
            name = item['labels'].get('en', 'no english title')
            matches = []
            for dist, i in item['osm']:
                osm_names = set([i['tags']['name']] + [v for k, v in i['tags'].items() if k.startswith('name:')])
                if any(name_match(o, w, endings[cat]) for o in osm_names for w in wikidata_names):
                    matches.append(i)
            if len(matches) != 1:
                continue
            item2 = copy(item)
            del item2['osm']
            wikidata_lookup[item['id']] = item2
            osm_lookup[(matches[0]['type'], matches[0]['id'])] = matches[0]
            all_matches[item['id']].add((matches[0]['type'], matches[0]['id']))
            num += 1
            if num % 100 == 0:
                print (num, name, item['id'], matches[0]['tags']['name'])
    out = open('match_list', 'w')
    multiple_osm_count = 0
    for wikidata_id, osm_matches in all_matches.iteritems():
        if len(osm_matches) != 1:
            multiple_osm_count += 1
            continue
        item = wikidata_lookup[wikidata_id]
        osm = osm_lookup[list(osm_matches)[0]]
        print >> out, (item, osm)
    out.close()

    print 'number of wikidata items that match multiple OSM objects with different entity types: {}'.format(multiple_osm_count)

if __name__ == '__main__':
    process()
