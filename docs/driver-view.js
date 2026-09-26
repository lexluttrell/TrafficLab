'use strict';
// A schematic ground-plane camera using recorded SUMO positions and lane geometry.
// It adds no terrain, buildings, measured camera footage or simulated dynamics.
const DriverView=(()=>{
 const cache=new WeakMap(),NEAR=.35,FAR=420;
 function camera(ego,width,height){const angle=ego[4]*Math.PI/180,forward=[Math.sin(angle),Math.cos(angle)],right=[Math.cos(angle),-Math.sin(angle)];return {x:ego[1]-forward[0]*2,z:ego[2]-forward[1]*2,forward,right,width,height,focal:Math.min(width*.78,height*1.15),horizon:height*.34,eye:1.5}}
 function transform(p,c){const dx=p[0]-c.x,dz=p[1]-c.z;return [dx*c.right[0]+dz*c.right[1],p[2]||0,dx*c.forward[0]+dz*c.forward[1]]}
 function project(p,c){return [c.width/2+p[0]*c.focal/p[2],c.horizon+(c.eye-p[1])*c.focal/p[2]]}
 function clip(vertices,limit,above){const out=[];if(!vertices.length)return out;let a=vertices.at(-1),insideA=above?a[2]>=limit:a[2]<=limit;for(const b of vertices){const insideB=above?b[2]>=limit:b[2]<=limit;if(insideA!==insideB){const f=(limit-a[2])/(b[2]-a[2]);out.push(a.map((v,i)=>v+(b[i]-v)*f))}if(insideB)out.push(b);a=b;insideA=insideB}return out}
 function polygon(ctx,vertices,c,fill,stroke){let pts=clip(clip(vertices,NEAR,true),FAR,false);if(pts.length<3)return;pts=pts.map(p=>project(p,c));ctx.beginPath();pts.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath();ctx.fillStyle=fill;ctx.fill();if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=.6;ctx.stroke()}}
 function mesh(data){if(cache.has(data))return cache.get(data);const strips=[],marks=[];for(const lane of [...data.lanes,...(typeof DriverGeometry!=='undefined'?DriverGeometry[data.meta.network_sha256]||[]:[])]){let distance=0;for(let i=1;i<lane.shape.length;i++){const a=lane.shape[i-1],b=lane.shape[i],len=Math.hypot(b[0]-a[0],b[1]-a[1]);if(len<.01)continue;const dx=(b[0]-a[0])/len,dy=(b[1]-a[1])/len,right=[dy,-dx],half=lane.width/2;for(let start=0;start<len;start+=10){const end=Math.min(start+10,len),p=[a[0]+dx*start,a[1]+dy*start],q=[a[0]+dx*end,a[1]+dy*end];strips.push({points:[[p[0]+right[0]*half,p[1]+right[1]*half,0],[q[0]+right[0]*half,q[1]+right[1]*half,0],[q[0]-right[0]*half,q[1]-right[1]*half,0],[p[0]-right[0]*half,p[1]-right[1]*half,0]],center:[(p[0]+q[0])/2,(p[1]+q[1])/2,0]})}
 // Dashed boundaries are illustrative markings, not a surveyed marking inventory.
 for(let start=Math.ceil(distance/9)*9-distance;start<len;start+=9){const end=Math.min(start+3,len);for(const side of [-1,1]){const sideOffset=side*half;marks.push([[a[0]+dx*start+right[0]*(sideOffset-.055),a[1]+dy*start+right[1]*(sideOffset-.055),.015],[a[0]+dx*end+right[0]*(sideOffset-.055),a[1]+dy*end+right[1]*(sideOffset-.055),.015],[a[0]+dx*end+right[0]*(sideOffset+.055),a[1]+dy*end+right[1]*(sideOffset+.055),.015],[a[0]+dx*start+right[0]*(sideOffset+.055),a[1]+dy*start+right[1]*(sideOffset+.055),.015]])}}distance+=len}}
 const result={strips,marks};cache.set(data,result);return result}
 function carFaces(car,c,color){
  const angle=car[4]*Math.PI/180,f=[Math.sin(angle),Math.cos(angle)],r=[Math.cos(angle),-Math.sin(angle)],center=[car[1]-2.5*f[0],car[2]-2.5*f[1]];
  const point=(x,z,y)=>transform([center[0]+x*r[0]+z*f[0],center[1]+x*r[1]+z*f[1],y],c);
  const quad=(coords,fill)=>({v:coords.map(p=>point(...p)),color:fill});
  const shade=(amount)=>'#'+color.slice(1).match(/../g).map(n=>Math.round(parseInt(n,16)*amount).toString(16).padStart(2,'0')).join('');
  const faces=[];
  // Group windows and lamps with their body panel so painter ordering cannot hide them.
  for(const side of [-1,1]){
   const z=side*2.5;
   const face=quad([[-1,z,.18],[1,z,.18],[1,z,.68],[-1,z,.68]],shade(.88));
   face.details=[quad([[-.9,z,.39],[-.54,z,.39],[-.54,z,.56],[-.9,z,.56]],side<0?'#ef746a':'#fff2c4'),quad([[.54,z,.39],[.9,z,.39],[.9,z,.56],[.54,z,.56]],side<0?'#ef746a':'#fff2c4')];faces.push(face);
   faces.push(quad([[-1,z,.68],[1,z,.68],[1,side*1.9,.68],[-1,side*1.9,.68]],color));
   const glass=quad([[-1,side*1.9,.68],[1,side*1.9,.68],[.82,side*1.15,1.42],[-.82,side*1.15,1.42]],color);
   glass.details=[quad([[-.8,side*1.78,.8],[.8,side*1.78,.8],[.67,side*1.24,1.33],[-.67,side*1.24,1.33]],'#163542')];faces.push(glass);
   faces.push(quad([[side,-2.5,.18],[side,2.5,.18],[side,2.5,.68],[side,-2.5,.68]],shade(.72)));
   const panel=quad([[side,-1.9,.68],[side,1.9,.68],[side*.82,1.15,1.42],[side*.82,-1.15,1.42]],shade(.8));
   panel.details=[quad([[side*.975,-1.64,.8],[side*.975,1.64,.8],[side*.845,1.08,1.32],[side*.845,-1.08,1.32]],'#173b48')];faces.push(panel);
  }
  faces.push(quad([[-.82,-1.15,1.42],[.82,-1.15,1.42],[.82,1.15,1.42],[-.82,1.15,1.42]],shade(.92)));
  return faces.sort((a,b)=>b.v.reduce((s,p)=>s+p[2],0)-a.v.reduce((s,p)=>s+p[2],0));
 }
 function draw(ctx,data,cars,ego,width,height,stats,mode){const sky=ctx.createLinearGradient(0,0,0,height*.52);sky.addColorStop(0,'#132937');sky.addColorStop(.8,'#56808d');sky.addColorStop(1,'#a2a894');ctx.fillStyle=sky;ctx.fillRect(0,0,width,height);const ground=ctx.createLinearGradient(0,height*.34,0,height);ground.addColorStop(0,'#49685e');ground.addColorStop(1,'#122d2b');ctx.fillStyle=ground;ctx.fillRect(0,height*.34,width,height*.66);if(!ego)return;
 const c=camera(ego,width,height),m=mesh(data);const strips=m.strips.map(s=>({s,p:transform(s.center,c)})).filter(o=>o.p[2]>-12&&o.p[2]<FAR+12&&Math.abs(o.p[0])<o.p[2]*1.7+35).sort((a,b)=>b.p[2]-a.p[2]);for(const {s,p}of strips){const light=Math.max(0,Math.min(1,p[2]/FAR));const gray=Math.round(42+light*22);polygon(ctx,s.points.map(p=>transform(p,c)),c,`rgb(${gray},${gray+13},${gray+20})`)}
 for(const mark of m.marks){const first=transform(mark[0],c);if(first[2]>-5&&first[2]<FAR&&Math.abs(first[0])<first[2]*1.7+30)polygon(ctx,mark.map(p=>transform(p,c)),c,'#c7d5cd')}
 const visible=cars.filter(v=>v[0]!==ego[0]).map(v=>({v,p:transform([v[1],v[2],0],c)})).filter(o=>o.p[2]>-3&&o.p[2]<FAR&&Math.abs(o.p[0])<o.p[2]*1.4+12).sort((a,b)=>b.p[2]-a.p[2]);for(const {v}of visible)for(const face of carFaces(v,c,FlowLayer.carColor(v,stats,mode))){polygon(ctx,face.v,c,face.color,'#132732');for(const detail of face.details||[])polygon(ctx,detail.v,c,detail.color)}
 const hood=ctx.createLinearGradient(0,height*.9,0,height);hood.addColorStop(0,'#244a53');hood.addColorStop(1,'#081821');ctx.fillStyle=hood;ctx.beginPath();ctx.moveTo(width*.16,height);ctx.quadraticCurveTo(width*.2,height*.88,width*.5,height*.895);ctx.quadraticCurveTo(width*.8,height*.88,width*.84,height);ctx.closePath();ctx.fill();ctx.strokeStyle='#668b9366';ctx.lineWidth=1;ctx.stroke();
 }
 return {draw,camera,transform,project,clip};
})();
if(typeof module!=='undefined')module.exports=DriverView;
