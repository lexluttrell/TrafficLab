"""Display-only local roads from the same OSM extract; never drive simulation."""
import xml.etree.ElementTree as ET
import gzip

def roads(source,net):
    if not source.exists(): source=source.with_suffix(source.suffix+'.gz')
    with (gzip.open(source,'rb') if source.suffix=='.gz' else source.open('rb')) as stream:
        root=ET.parse(stream).getroot()
    nodes={n.attrib['id']:(float(n.attrib['lon']),float(n.attrib['lat'])) for n in root.findall('node')}
    result=[]
    for way in root.findall('way'):
        tags={t.attrib['k']:t.attrib['v'] for t in way.findall('tag')}
        if tags.get('highway') not in ('primary','secondary','tertiary','residential','unclassified'):continue
        points=[nodes[n.attrib['ref']] for n in way.findall('nd') if n.attrib['ref'] in nodes]
        if len(points)>1:result.append({'name':tags.get('name',''),'shape':[net.convertLonLat2XY(*p) for p in points]})
    return result
