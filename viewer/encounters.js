/* Recorded trajectories only. No simulated behavior or causal effect is generated here. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const C = {actor:'#73e3c5',follower:'#f6be70',other:'#748b9b',rose:'#ff98b3',grid:'#2a404e',text:'#91a9b9'};
  let audit, data, frame=0, playing=false, last=0, accumulator=0, loadVersion=0;
  const fmt = (v,n=1) => v == null ? '—' : v.toFixed(n);
  const flagNames = {leader_unavailable:'No usable reported leader in this sample',leader_lane_mismatch:'Reported leader is in a different lane',negative_net_gap:'Negative computed gap',speed_below_time_gap_threshold:'Too slow for a stable time-gap measure',position_speed_disagreement:'Positions and reported speed disagree',source_spacing_disagreement:'Reported spacing and positions disagree',track_discontinuity:'Observation discontinuity',invalid_dimensions_or_speed:'Invalid dimensions or speed',follower_not_observed:'Follower is not observed at this time'};
  function fit(canvas) {
    const box=canvas.getBoundingClientRect(), dpr=Math.min(devicePixelRatio||1,2);
    if(canvas.width!==Math.round(box.width*dpr)||canvas.height!==Math.round(box.height*dpr)){canvas.width=Math.round(box.width*dpr);canvas.height=Math.round(box.height*dpr);}
    const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,box.width,box.height);
    return [ctx,box.width,box.height];
  }
  function pause(){playing=false;$('play').textContent='Play';}
  function seek(t){if(!data)return;frame=Math.max(0,Math.min(data.frames.length-1,Math.round((t-data.frames[0][0])*10)));accumulator=0;render();}
  function drawRoad(){
    const [ctx,w,h]=fit($('road')), cars=data.frames[frame][1];
    const actor=cars.find(c=>c[0]===data.event.actor), follower=cars.find(c=>c[0]===data.event.follower);
    const focus=follower||actor;
    if(!focus){ctx.fillStyle=C.text;ctx.font='12px system-ui';ctx.textAlign='center';ctx.fillText('No focal vehicle observed at this time',w/2,h/2);return;}
    const left=52,right=w-25,lanew=(right-left)/7, sy=(h-60)/160;
    const X=x=>left+x/3.66*lanew, Y=y=>h*.64-(y-focus[2])*sy;
    ctx.fillStyle='#172b36';ctx.fillRect(left,0,right-left,h);
    for(let lane=0;lane<=7;lane++){ctx.strokeStyle=lane===0||lane===6?'#647780':'#3c505d';ctx.setLineDash(lane===0||lane===6?[]:[8,11]);ctx.beginPath();ctx.moveTo(left+lane*lanew,0);ctx.lineTo(left+lane*lanew,h);ctx.stroke();}
    ctx.setLineDash([]);ctx.font='9px system-ui';ctx.fillStyle=C.text;ctx.textAlign='center';
    for(let lane=1;lane<=7;lane++)ctx.fillText(lane===7?'Ramp':`L${lane}`,left+(lane-.5)*lanew,17);
    for(let d=-40;d<=80;d+=20){const y=Y(focus[2]+d);ctx.fillStyle=C.text;ctx.textAlign='right';ctx.fillText(`${d>0?'+':''}${d} m`,45,y+3);ctx.strokeStyle='#263e4c';ctx.lineWidth=.5;ctx.beginPath();ctx.moveTo(left,y);ctx.lineTo(right,y);ctx.stroke();}
    if(follower){const leader=cars.find(c=>c[0]===follower[7]);if(leader&&leader[6]===follower[6]){ctx.strokeStyle=C.follower;ctx.lineWidth=1.5;ctx.setLineDash([3,4]);ctx.beginPath();ctx.moveTo(X(follower[1]),Y(follower[2]));ctx.lineTo(X(leader[1]),Y(leader[2]-leader[3]));ctx.stroke();ctx.setLineDash([]);}}
    for(const car of [...cars.filter(c=>c[0]!==data.event.actor&&c[0]!==data.event.follower),...cars.filter(c=>c[0]===data.event.actor||c[0]===data.event.follower)]){
      const isActor=car[0]===data.event.actor,isFollower=car[0]===data.event.follower;
      const x=X(car[1]), y=Y(car[2]), width=Math.max(4,car[4]/3.66*lanew), length=Math.max(5,car[3]*sy);
      if(y>h+length||y+length<0)continue;
      ctx.fillStyle=isActor?C.actor:isFollower?C.follower:C.other;ctx.globalAlpha=isActor||isFollower?1:.65;ctx.fillRect(x-width/2,y,width,length);
      ctx.fillStyle='#0d2029';ctx.fillRect(x-width*.36,y+Math.min(length*.25,4),width*.72,Math.min(length*.2,3));ctx.globalAlpha=1;
      if(isActor||isFollower){ctx.strokeStyle='#e5f4ef';ctx.lineWidth=1;ctx.strokeRect(x-width/2-2,y-2,width+4,length+4);ctx.font='bold 10px system-ui';ctx.fillStyle=isActor?C.actor:C.follower;ctx.textAlign='center';ctx.fillText(`${isActor?'A':'F'} ${car[0]}`,x,y-7);}
    }
    ctx.fillStyle='#10212ae8';ctx.fillRect(0,h-24,w,24);ctx.textAlign='left';ctx.font='10px system-ui';ctx.fillStyle=C.text;ctx.fillText(`Following ${follower?'F '+follower[0]:'actor · follower unavailable'} · source step 0.1 s`,10,h-8);
  }
  function drawChart(id, keys, unitsFactor=1){
    const [ctx,w,h]=fit($(id)), p={l:35,r:10,t:10,b:23};
    const minT=data.series[0].t,maxT=data.series.at(-1).t;
    const values=data.series.flatMap(r=>keys.map(k=>r[k]).filter(v=>v!=null&&Number.isFinite(v))).map(v=>v*unitsFactor);
    const max=Math.max(1,...values)*1.12, x=t=>p.l+(t-minT)/(maxT-minT)*(w-p.l-p.r), y=v=>h-p.b-v/max*(h-p.b-p.t);
    ctx.fillStyle='#152c35';ctx.fillRect(x(0),p.t,x(maxT)-x(0),h-p.t-p.b);
    ctx.font='9px system-ui';ctx.lineWidth=1;ctx.textAlign='right';
    for(let i=0;i<=3;i++){const v=max*i/3;ctx.fillStyle=C.text;ctx.fillText(v.toFixed(max>15?0:1),p.l-6,y(v)+3);ctx.strokeStyle=C.grid;ctx.beginPath();ctx.moveTo(p.l,y(v));ctx.lineTo(w-p.r,y(v));ctx.stroke();}
    ctx.textAlign='center';for(let t=Math.ceil(minT/10)*10;t<=maxT;t+=10){ctx.fillStyle=C.text;ctx.fillText(`${t>0?'+':''}${t}s`,x(t),h-6);}
    ctx.strokeStyle='#658291';ctx.setLineDash([3,4]);ctx.beginPath();ctx.moveTo(x(0),p.t);ctx.lineTo(x(0),h-p.b);ctx.stroke();ctx.setLineDash([]);
    keys.forEach((key,ki)=>{ctx.strokeStyle=keys.length===2&&ki===0?C.actor:C.follower;ctx.lineWidth=1.5;ctx.beginPath();let pen=false;for(const row of data.series){const v=row[key];if(v==null){pen=false;continue;}if(pen)ctx.lineTo(x(row.t),y(v*unitsFactor));else ctx.moveTo(x(row.t),y(v*unitsFactor));pen=true;}ctx.stroke();});
    if(keys.length===1){ctx.strokeStyle='#f6be7055';ctx.setLineDash([2,5]);for(let i=1;i<data.series.length;i++){const r=data.series[i],previous=data.series[i-1];if(r.leader&&previous.leader&&r.leader!==previous.leader){ctx.beginPath();ctx.moveTo(x(r.t),p.t);ctx.lineTo(x(r.t),h-p.b);ctx.stroke();}}ctx.setLineDash([]);ctx.fillStyle=C.rose;for(const row of data.series){if(!row.gap_usable&&row[keys[0]]!=null){ctx.fillRect(x(row.t)-.8,y(row[keys[0]]*unitsFactor)-.8,1.6,1.6);}}}
    const t=data.series[frame].t;ctx.strokeStyle='#e8eff2';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x(t),p.t);ctx.lineTo(x(t),h-p.b);ctx.stroke();
  }
  function render(){if(!data)return;const r=data.series[frame];$('timeline').value=r.t;$('clock').textContent=`${r.t>=0?'+':''}${r.t.toFixed(1)} s`;$('current-speed').textContent=fmt(r.follower_speed==null?null:r.follower_speed*2.236936);$('current-gap').textContent=fmt(r.gap);$('current-headway').textContent=fmt(r.time_gap,2);$('current-leader').textContent=`Current leader: ${r.leader||'unavailable'} · follower lane: ${r.follower_lane||'unavailable'}`;$('quality-now').textContent=r.flags.length?'At this moment: '+r.flags.map(f=>flagNames[f]||f).join(' · '):'At this moment: no implemented measurement screen is flagged. This is not independent validation.';drawRoad();drawChart('speed-chart',['actor_speed','follower_speed'],2.236936);drawChart('gap-chart',['gap']);drawChart('headway-chart',['time_gap']);}
  async function load(i){
    const version=++loadVersion;pause();data=null;for(const id of ['road','speed-chart','gap-chart','headway-chart'])fit($(id));for(const id of ['current-speed','current-gap','current-headway','clock'])$(id).textContent='—';$('current-leader').textContent='';$('play').disabled=true;$('timeline').disabled=true;$('event-zero').disabled=true;$('load-status').textContent='Loading observed tracks…';
    const item=audit.encounters[i],url='encounter-data/'+item.file;
    try{
      const response=await fetch(url);if(!response.ok)throw Error(`Data request: ${response.status}`);
      const bytes=await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
      const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(b=>b.toString(16).padStart(2,'0')).join('');
      if(digest!==item.sha256_uncompressed)throw Error('Encounter checksum does not match the audit');
      const next=JSON.parse(new TextDecoder().decode(bytes));if(version!==loadVersion)return;data=next;
      $('timeline').min=data.series[0].t;$('timeline').max=data.series.at(-1).t;$('time-start').textContent=`${data.series[0].t} s`;$('time-end').textContent=`+${data.series.at(-1).t} s`;
      $('event-title').textContent=`Vehicle ${item.actor} moves from lane ${item.old_lane} to ${item.new_lane}`;
      $('event-description').textContent=`Follower ${item.follower} is directly behind it in the destination lane at the transition. ${item.repeated_candidate?'This actor has another stable mainline lane change within 30 seconds; discretionary intent is unverified.':'This selected transition is not part of a repeated-change candidate within 30 seconds.'} ${item.selection_role.startsWith('supplemental')?'Supplemental exploratory example; an earlier lane change is present.':''} Stable actor transitions relative to this event: ${item.nearby_actor_changes_s.map(t=>(t>0?'+':'')+t.toFixed(1)+' s').join(', ')}.`;
      $('coverage').replaceChildren();for(const seconds of [10,30]){const a=item.coverage[`actor_${seconds}s`],f=item.coverage[`follower_${seconds}s`],ok=a.continuous&&f.continuous;const chip=document.createElement('span');chip.className='chip'+(ok?'':' warn');chip.textContent=`±${seconds} s: ${ok?'both tracks continuous':'incomplete track coverage'}`;$('coverage').append(chip);}
      const pre=data.series.filter(r=>r.t<0),post=data.series.filter(r=>r.t>0),validPre=pre.filter(r=>r.gap_usable).length,validPost=post.filter(r=>r.gap_usable).length;
      $('gap-coverage').textContent=`Usable follower time-gap samples: before ${validPre}/${pre.length}; after ${validPost}/${post.length}. ${validPre===0?'No usable pre-event gap baseline: this example cannot support a before/after following-gap estimate.':'Continuous tracking alone does not guarantee usable gap measurements.'}`;
      const counts={};for(const r of data.series)for(const flag of r.flags)counts[flag]=(counts[flag]||0)+1;
      const ul=document.createElement('ul');for(const [flag,count] of Object.entries(counts)){const li=document.createElement('li');li.textContent=`${flagNames[flag]||flag}: ${count} / ${data.series.length} follower samples`;ul.append(li);}$('window-flags').replaceChildren(ul);
      $('download').href=url;$('download').download=item.file;$('load-status').textContent='Observed data loaded · checksum verified · paused at the lane change';$('play').disabled=false;$('timeline').disabled=false;$('event-zero').disabled=false;seek(0);
    }catch(error){if(version===loadVersion){data=null;$('load-status').textContent=`Could not load encounter: ${error.message}. Reload to retry.`;}}
  }
  $('play').addEventListener('click',()=>{if(!data)return;if(playing)pause();else{if(frame===data.frames.length-1)seek(data.frames[0][0]);playing=true;last=performance.now();$('play').textContent='Pause';$('load-status').textContent='Playing recorded observations';}});
  $('event-zero').addEventListener('click',()=>{pause();seek(0);});$('timeline').addEventListener('input',e=>{pause();seek(Number(e.target.value));});$('encounter').addEventListener('change',e=>load(Number(e.target.value)));
  for(const id of ['speed-chart','gap-chart','headway-chart']){
    $(id).addEventListener('click',e=>{if(!data)return;const rect=e.currentTarget.getBoundingClientRect();pause();seek(data.series[0].t+(e.clientX-rect.left-35)/(rect.width-45)*(data.series.at(-1).t-data.series[0].t));});
    $(id).addEventListener('keydown',e=>{if(!data||!['ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();pause();seek(data.series[frame].t+(e.key==='ArrowRight'?1:-1));});
  }
  document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});window.addEventListener('resize',render);
  function tick(now){if(playing&&data){accumulator+=Math.min(now-last,200)*Number($('rate').value);if(accumulator>=100){const n=Math.floor(accumulator/100);accumulator%=100;frame=Math.min(data.frames.length-1,frame+n);if(frame===data.frames.length-1){pause();$('load-status').textContent='End of observed window';}render();}}last=now;requestAnimationFrame(tick);}requestAnimationFrame(tick);
  (async()=>{try{const response=await fetch('encounter-data/index.json');if(!response.ok)throw Error(`Audit request: ${response.status}`);audit=await response.json();$('n-vehicles').textContent=audit.vehicles.toLocaleString();$('n-events').textContent=audit.candidate_funnel.stable_mainline_transitions||0;$('n-pairs').textContent=audit.candidate_funnel.inspectable_10s_pairs||0;$('n-long').textContent=audit.candidate_funnel.continuous_30s_pairs||0;$('clock-note').textContent=audit.clock_note;$('sample-conclusion').textContent=`This sample contains ${audit.candidate_funnel.inspectable_repeated_10s_pairs||0} repeated-change candidate transitions with verified follower relations and continuous ±10-second tracks. These are development observations, not independent experiments or a measured behavioral effect.`;audit.encounters.forEach((e,i)=>{const option=document.createElement('option');option.value=i;option.textContent=e.selection_role.startsWith('supplemental')?`${i+1} · repeated changes`:`${i+1} · ${e.actor} → lane ${e.new_lane}`;$('encounter').append(option);});if(!audit.encounters.length){$('load-status').textContent='No encounter passed the inspection screen. The audit remains available below.';return;}$('encounter').disabled=false;await load(0);}catch(error){$('load-status').textContent=`Could not load the study: ${error.message}. Reload to retry.`;}})();
})();
