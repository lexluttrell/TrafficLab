"""Synthetic through-demand: choose longest connected motorway route each direction."""
import xml.etree.ElementTree as ET
import sumolib
import heapq


def build(network, output, config):
    net = sumolib.net.readNet(str(network))
    edges = [e for e in net.getEdges() if e.getType() == 'highway.motorway' and e.allows('passenger')]
    # Mainline boundary edges only: ramps are retained in geometry but carry no demand.
    ids = {e.getID() for e in edges}
    starts = [e for e in edges if not any(p.getID() in ids for p in e.getIncoming())]
    ends = [e for e in edges if not any(p.getID() in ids for p in e.getOutgoing())]
    candidates = []
    for a in starts:
        for b in ends:
            queue = [(a.getLength(), a.getID(), [a])]
            seen = set()
            route = None
            while queue:
                cost, eid, path = heapq.heappop(queue)
                if eid in seen: continue
                seen.add(eid)
                if eid == b.getID():
                    route = path
                    break
                for edge, connections in path[-1].getOutgoing().items():
                    if edge.getID() in ids and edge.getID() not in seen and any(c.getFromLane().allows('passenger') and c.getToLane().allows('passenger') for c in connections):
                        heapq.heappush(queue, (cost+edge.getLength(), edge.getID(), path+[edge]))
            if route and len(route) > 1 and all(e.getID() in ids for e in route):
                candidates.append((sum(e.getLength() for e in route), route))
    routes = []
    used = set()
    for length, route in sorted(candidates, key=lambda x: x[0], reverse=True):
        route_ids = {e.getID() for e in route}
        if not used.intersection(route_ids):
            routes.append((length, route)); used.update(route_ids)
        if len(routes) == 2: break
    if len(routes) != 2:
        raise ValueError('Could not find two disjoint mainline routes. Inspect the source extent and network.')
    root = ET.Element('routes')
    ET.SubElement(root, 'vType', id='synthetic-car', vClass='passenger', carFollowModel='Krauss',
                  accel='2.6', decel='4.5', sigma='0.5', tau='1.0', length='5', minGap='2.5', maxSpeed='33.33')
    summary=[]
    for i, (length, route) in enumerate(routes):
        rid = f'through-{i}'
        ET.SubElement(root, 'route', id=rid, edges=' '.join(e.getID() for e in route))
        ET.SubElement(root, 'flow', id=f'car-{i}', type='synthetic-car', route=rid, begin='0',
                      end=str(config['demand_end']), vehsPerHour=str(config['vehicles_per_hour_per_direction']),
                      departLane='best', departSpeed='max')
        summary.append({'id':rid,'length_m':length,'edges':[e.getID() for e in route]})
    ET.ElementTree(root).write(output, encoding='utf-8', xml_declaration=True)
    return net, summary
