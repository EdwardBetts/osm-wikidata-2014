import jinja2
import codecs

env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
matches = (eval(line) for line in open('match_list'))

template = env.get_template('matches.html')
out = codecs.open('osm_wikidata_match.html', 'w', 'utf-8')
for buf in template.generate(matches=matches):
    out.write(buf)
out.close()
