const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
function setup(network,stored,cacheError){
  const handlers={};const writes=[];
  const context={URL,self:{addEventListener:(name,fn)=>handlers[name]=fn},fetch:network,caches:{match:async()=>stored,open:async()=>({put:async(request,response)=>{if(cacheError)throw cacheError;writes.push(response);}})}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../product/sw.js'),'utf8'),context);
  return {writes,request:async(url='https://synthetic.test/',mode='navigate')=>{let result;handlers.fetch({request:{url,mode},respondWith:p=>result=p});return result;}};
}
test('online navigation returns and caches fresh page instead of stale page',async()=>{
  const fresh={ok:true,clone(){return this;}};const worker=setup(async()=>fresh,{stale:true});
  assert.equal(await worker.request(),fresh);assert.deepEqual(worker.writes,[fresh]);
});
test('offline navigation uses cached page and rejects when none is stored',async()=>{
  const error=Error('synthetic offline');const cached={saved:true};
  assert.equal(await setup(async()=>{throw error;},cached).request(),cached);
  await assert.rejects(setup(async()=>{throw error;}).request(),error);
});
test('HTTP errors are not replaced or cached; API stays network-only',async()=>{
  const response={ok:false};const worker=setup(async()=>response,{stale:true});
  assert.equal(await worker.request(),response);assert.equal(worker.writes.length,0);
  const error=Error('API offline');const api=setup(async()=>{throw error;},{stale:true});
  await assert.rejects(api.request('https://synthetic.test/api/save','cors'),error);
});

test('cache write failure cannot replace a fresh online page with stale content',async()=>{
  const fresh={ok:true,clone(){return this;}};
  assert.equal(await setup(async()=>fresh,{stale:true},Error('synthetic quota')).request(),fresh);
});
