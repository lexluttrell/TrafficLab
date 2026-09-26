'use strict';
// Snapshot means, never detector estimates. Edge IDs separate ramps and directions.
const FlowLayer=(()=>{
const MPH=2.236936,WIDTH=100,cache=new WeakMap();
const key=v=>v[5].replace(/_\d+$/,'')+':'+Math.floor(v[6]/WIDTH);
function aggregate(cars){const groups=new Map();for(const v of cars){const k=key(v),g=groups.get(k)||{sum:0,n:0};g.sum+=v[3];g.n++;groups.set(k,g)}return groups}
function peer(v,groups){const g=groups.get(key(v));return g&&g.n>=3?{mean:(g.sum-v[3])/(g.n-1),count:g.n-1}:null}
function speedColor(v){const m=v*MPH;return m<20?'#d85a49':m<40?'#c89b35':m<55?'#89aa48':'#398c70'}
function carColor(v,groups,mode){if(mode==='absolute'){const m=v[3]*MPH;return m<20?'#ff876e':m<40?'#ffcf69':m<55?'#bfe77c':'#79f4cc'}const p=peer(v,groups);if(!p)return '#8c9eac';const delta=(v[3]-p.mean)*MPH;return delta>5?'#50dfff':delta< -5?'#df9cff':'#f2f4ed'}
function peerText(v,groups){const p=peer(v,groups);if(!p)return 'Fewer than 2 nearby peers';const delta=(v[3]-p.mean)*MPH;return `${delta>=0?'+':''}${delta.toFixed(1)} mph vs ${p.count} peers`}
function segments(lane){if(cache.has(lane))return cache.get(lane);const pts=lane.shape,lens=[0];for(let i=1;i<pts.length;i++)lens.push(lens[i-1]+Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]));const length=lane.length_m||lens.at(-1),factor=lens.at(-1)/length,result=[];function at(d){let i=1;while(i<lens.length-1&&lens[i]<d)i++;const f=(d-lens[i-1])/(lens[i]-lens[i-1]||1);return [pts[i-1][0]+f*(pts[i][0]-pts[i-1][0]),pts[i-1][1]+f*(pts[i][1]-pts[i-1][1])]}
for(let a=0;a<length;a+=WIDTH){const lo=a*factor,hi=Math.min(length,a+WIDTH)*factor,shape=[at(lo)];for(let i=1;i<pts.length-1;i++)if(lens[i]>lo&&lens[i]<hi)shape.push(pts[i]);shape.push(at(hi));result.push({key:lane.id.replace(/_\d+$/,'')+':'+Math.floor(a/WIDTH),shape})}cache.set(lane,result);return result}
function drawRoads(ctx,lanes,screen,scale,groups,enabled){for(const lane of lanes){for(const segment of segments(lane)){ctx.beginPath();segment.shape.forEach((p,i)=>{const q=screen(...p);i?ctx.lineTo(...q):ctx.moveTo(...q)});const g=groups.get(segment.key);ctx.strokeStyle=enabled&&g?speedColor(g.sum/g.n):'#354752';ctx.lineWidth=Math.max(enabled&&g?6:1,lane.width*scale);ctx.stroke()}}}
function legend(mode,roads){return (roads?'<span>Road mean: <b style="color:#ed796a">&lt;20</b> · <b style="color:#e9bc51">20–40</b> · <b style="color:#bada73">40–55</b> · <b style="color:#69d4ac">55+ mph</b> · gray: no cars</span>':'<span>Road speed layer off</span>')+(mode==='absolute'?'<span>Cars: absolute speed · &lt;20 / 20–40 / 40–55 / 55+ mph</span>':'<span>Cars vs peers: <b style="color:#df9cff">slower</b> · <b style="color:#f2f4ed">within ±5 mph</b> · <b style="color:#50dfff">faster</b> · gray: &lt;2 peers</span>')}
return {aggregate,peer,peerText,carColor,speedColor,drawRoads,legend};
})();
if(typeof module!=='undefined')module.exports=FlowLayer;
