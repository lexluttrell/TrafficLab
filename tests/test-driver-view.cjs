const assert=require('node:assert/strict');const D=require('../viewer/driver-view.js');
const ego=['car',100,200,20,0,'lane',0,0],c=D.camera(ego,1000,600);
assert.deepEqual(D.transform([100,208,0],c),[0,0,10]);
const center=D.project([0,0,10],c);assert.equal(center[0],500);assert(center[1]>c.horizon);
assert(D.project([2,0,10],c)[0]>500);
const east=D.camera([...ego.slice(0,4),90],1000,600);assert(Math.abs(D.transform([110,200,0],east)[0])<1e-8);
const clipped=D.clip([[-1,0,-2],[1,0,3],[-1,0,3]],1.2,true);assert(clipped.length>=3);assert(clipped.every(p=>p[2]>=1.2-1e-10));
assert.deepEqual(D.clip([[0,0,-3],[1,0,-2],[2,0,-1]],1.2,true),[]);
console.log('PASS: north/east camera orientation, centered projection, right-hand screen direction and near-plane clipping');
