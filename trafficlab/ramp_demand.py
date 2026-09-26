"""Graph-checked ramp movements and explicitly uncertain exit demand.

Region-specific bindings and estimation relationships live in scenario JSON.
"""
from datetime import timedelta
import random
import xml.etree.ElementTree as ET


def connected(net, edges):
    for a,b in zip(edges,edges[1:]):
        choices=net.getEdge(a).getOutgoing().get(net.getEdge(b),[])
        if not any(c.getFromLane().allows('passenger') and c.getToLane().allows('passenger') for c in choices):
            raise ValueError(f'No passenger connection {a} -> {b}')


def estimate_fraction(upstream, added, downstream):
    available=upstream+added
    if available<=0:raise ValueError('Cannot estimate exit fraction with zero available flow')
    raw=(available-downstream)/available
    return max(0,min(.8,raw)),raw


def build_ramps(net, through_routes, stations, rows, start, config, root, seed):
    from .historical import build_departures
    rng=random.Random(seed);movements=[];inputs=[];audit=[];route_defs={};geometry=[];estimates=[]
    duration=config['duration_seconds'];enabled=config['demand_mode']=='ramps'
    def record(sid,begin):
        stamp=(start+timedelta(seconds=begin)).isoformat();r=rows.get((sid,stamp))
        if r is None or r['flow_vehicles_per_5min'] is None:raise ValueError(f'Missing required flow {sid} {stamp}')
        return r
    def total(sids):return sum(record(s,b)['flow_vehicles_per_5min'] for s in sids for b in range(0,duration,300))
    fractions={}
    for event in config['ramp_events']:
        sid=event['station'];s=stations[sid]
        if s['direction']!=event['direction'] or s['type']!=('OR' if event['kind']=='entry' else 'FR'):
            raise ValueError('Ramp metadata direction/type mismatch: '+sid)
        connected(net,event['edges'])
        if event['kind']=='entry' and net.getEdge(event['edges'][0]).getLaneNumber()!=s['lanes']:
            raise ValueError('Ramp entry lane inventory mismatch: '+sid)
        if 'estimate' in event:
            e=event['estimate'];up,add,down=total(e['upstream']),total(e['add']),total(e['downstream'])
            fraction,raw=estimate_fraction(up,add,down);fractions[sid]=min(.95,fraction*config['exit_multiplier'])
            estimates.append({'station':sid,'hour_upstream':up,'hour_added':add,'hour_downstream':down,
                              'raw_fraction':raw,'base_fraction':fraction,'applied_fraction':fractions[sid],
                              'constrained':raw!=fraction,'method':'hour-total balance assumes negligible storage change; no travel-time alignment; capped [0,0.8] before sensitivity multiplier',
                              'source_stations':e,'status':'inferred scenario assumption, not a measurement'})
    def finish(vehicle,edges,dest):
        connected(net,edges);key=tuple(edges)
        if key not in route_defs:
            rid='route-'+str(len(route_defs));route_defs[key]=rid
            ET.SubElement(root,'route',id=rid,edges=' '.join(edges))
            geometry.append({'id':rid,'edges':edges,'origin_station':vehicle['origin'],'destination':dest})
        movements.append({**vehicle,'route':route_defs[key],'destination':dest})
    for sid in config['input_stations']:
        station=stations[sid];candidate=station['mapping_candidates'][0];direction=station['direction']
        route=next(r['edges'] for r in through_routes if candidate['edge'] in r['edges'])
        main=route[route.index(candidate['edge']):route.index(config['mainline_end_edges'][direction])+1]
        if not main:raise ValueError('Invalid mainline limits')
        if candidate['distance_m']>15 or candidate['network_lanes']!=station['lanes']:raise ValueError('Invalid mainline entry binding')
        events=[]
        for event in config['ramp_events']:
            if event['direction']!=direction:continue
            e=net.getEdge(event['edges'][-1] if event['kind']=='entry' else event['edges'][0])
            neighbors=e.getOutgoing() if event['kind']=='entry' else e.getIncoming()
            found=[i for i,eid in enumerate(main) if net.getEdge(eid) in neighbors]
            if len(found)!=1:raise ValueError('Ramp has no unique mainline connection: '+event['station'])
            events.append((found[0]*2+(event['kind']=='exit'),found[0],event))
        for begin in range(0,duration,300):
            available=[]
            def enter(origin,edges,index,pos):
                obs=record(origin,begin);times=build_departures(obs['flow_vehicles_per_5min'],begin,random.Random(f'{seed}:{origin}:{begin}'))
                inputs.append({'station_id':origin,'begin':begin,'timestamp_local':obs['timestamp_local'],
                               'reported_count':obs['flow_vehicles_per_5min'],'scheduled_count':len(times),
                               'percent_observed':obs['percent_observed'],'quality_flags':obs['quality_flags'],
                               'kind':'mainline' if origin==sid else 'ramp'})
                for j,t in enumerate(times):available.append({'id':f'o{origin}-{begin}-{j}','depart':t,'origin':origin,'prefix':edges,'main_index':index,'pos':pos,'begin':begin})
            enter(sid,[],0,candidate['offset_m']+10)
            for _,index,event in sorted(events,key=lambda e:e[0]):
                if not enabled:continue
                origin=event['station']
                if event['kind']=='entry':enter(origin,event['edges'],index,20)
                else:
                    available_count=len(available)
                    if 'estimate' in event:
                        target=int(available_count*fractions[origin]+.5);source='inferred fraction'
                    else:target=int(record(origin,begin)['flow_vehicles_per_5min']+.5);source='reported count, applied to departure cohort'
                    count=min(target,available_count);selected=rng.sample(available,count)
                    ids={v['id'] for v in selected};available=[v for v in available if v['id'] not in ids]
                    for v in selected:finish(v,v['prefix']+main[v['main_index']:index+1]+event['edges'],origin)
                    audit.append({'station_id':origin,'begin':begin,'source':source,'target':target,'assigned':count,
                                  'available':available_count,'clipped':target-count})
            for v in available:finish(v,v['prefix']+main[v['main_index']:], 'boundary-'+direction)
    for v in sorted(movements,key=lambda v:(v['depart'],v['id'])):
        ET.SubElement(root,'vehicle',id=v['id'],type='baseline-car',route=v['route'],depart=f"{v['depart']:.3f}",
                      departPos=str(v['pos']),departLane='best',departSpeed='max')
    # Movement tables retain the distinction between prescribed demand and actual crossing time.
    return movements,inputs,geometry,{'mode':config['demand_mode'],'exit_multiplier':config['exit_multiplier'],
                                    'estimates':estimates,'exit_targets':audit,'bindings':config['ramp_events'],
                                    'fit_stations':config['fit_stations'],
                                    'limitations':['Ramp endpoints are model boundaries, not measured detector positions.',
                                      'Route exits are assigned by source departure bin; actual passage can occur in a later bin.',
                                      'No ramp signal/metering, arterial queues, or congestion beyond the corridor is imposed.',
                                      'Exit multipliers are sensitivity scenarios, not confidence intervals.']}
