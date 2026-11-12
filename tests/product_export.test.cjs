const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
function setup(){
  const source=fs.readFileSync(path.join(__dirname,'../product/index.html'),'utf8').match(/async function finishSession\([^]*?\n}/)[0];
  const answer={value:'synthetic answer'};const lost={hidden:true};const shown=[];const alerts=[];
  const context=vm.createContext({state:{sessionId:'synthetic',exportData:{stale:true}},document:{getElementById:id=>id==='sessionLost'?lost:answer},show:id=>shown.push(id),alert:m=>alerts.push(m)});
  vm.runInContext(source,context);return {context,answer,lost,shown,alerts};
}
test('failed answer/save stays retryable and never completes with stale export',async()=>{
  for(const failingPath of ['/api/deeper','/api/save']){
    const {context,answer,shown,alerts}=setup();const calls=[];
    context.api=async path=>{calls.push(path);if(path===failingPath)throw Error('synthetic failure');return {};};
    await context.finishSession();
    assert.equal(shown.length,0);assert.equal(alerts.length,1);assert.equal(context.state.exportData,null);assert.equal(answer.value,'synthetic answer');
    const saved={meta:{me:'synthetic'}};context.api=async()=>({session_data:saved});
    await context.finishSession();assert.deepEqual(shown,['step-complete']);assert.equal(context.state.exportData,saved);
    assert.equal(calls.includes('/api/save'),failingPath==='/api/save');
  }
});
test('missing or malformed export payload cannot show completion',async()=>{
  for(const value of [undefined,null,'invalid',[]]){
    const {context,shown,alerts}=setup();context.api=async()=>({session_data:value});
    await context.finishSession();assert.equal(shown.length,0);assert.equal(alerts.length,1);assert.equal(context.state.exportData,null);
  }
});
test('blank answer still exports directly and completes only with a result',async()=>{
  const {context,answer,shown}=setup();answer.value='';const calls=[];const saved={responses:[]};context.api=async path=>{calls.push(path);return {session_data:saved};};
  await context.finishSession();assert.deepEqual(calls,['/api/save']);assert.deepEqual(shown,['step-complete']);assert.equal(context.state.exportData,saved);
});

test('missing session during answer or export shows recovery without losing answer',async()=>{
  for(const failingPath of ['/api/deeper','/api/save']){
    const {context,answer,lost,shown,alerts}=setup();
    context.api=async path=>{if(path===failingPath){const e=Error('missing session');e.status=404;throw e;}return {};};
    await context.finishSession();
    assert.equal(lost.hidden,false);assert.equal(answer.value,'synthetic answer');
    assert.equal(context.state.exportData,null);assert.deepEqual(shown,[]);assert.deepEqual(alerts,[]);
  }
});
test('503 stays retryable and clears prior missing-session notice',async()=>{
  const {context,lost,alerts}=setup();lost.hidden=false;
  context.api=async()=>{const e=Error('temporarily unavailable');e.status=503;throw e;};
  await context.finishSession();assert.equal(lost.hidden,true);assert.equal(alerts.length,1);
});
test('missing-session restart requires explicit confirmation',()=>{
  const source=fs.readFileSync(path.join(__dirname,'../product/index.html'),'utf8').match(/function restartLostSession\([^]*?\n}/)[0];
  let reloads=0;const warnings=[];let approved=false;
  const ctx=vm.createContext({confirm:text=>{warnings.push(text);return approved;},location:{reload:()=>reloads++}});
  vm.runInContext(source,ctx);ctx.restartLostSession();assert.equal(reloads,0);
  approved=true;ctx.restartLostSession();assert.equal(reloads,1);assert.match(warnings[0],/사라집니다/);assert.match(warnings[0],/복사/);
});
test('api preserves HTTP status and rejects non-OK responses even without error text',async()=>{
  const source=fs.readFileSync(path.join(__dirname,'../product/index.html'),'utf8').match(/async function api\([^]*?\n}/)[0];
  for(const status of [404,503]){
    const ctx=vm.createContext({fetch:async()=>({ok:false,status,json:async()=>({})})});vm.runInContext(source,ctx);
    await assert.rejects(ctx.api('/api/save',{}),e=>e.status===status);
  }
});
test('successful finish hides an earlier missing-session notice',async()=>{
  const {context,lost,shown}=setup();lost.hidden=false;
  context.api=async()=>({session_data:{demo:true}});
  await context.finishSession();assert.equal(lost.hidden,true);assert.deepEqual(shown,['step-complete']);
});
test('non-JSON HTTP error stays a generic failure without a status claim',async()=>{
  const apiSource=fs.readFileSync(path.join(__dirname,'../product/index.html'),'utf8').match(/async function api\([^]*?\n}/)[0];
  const {context,lost,answer,alerts,shown}=setup();
  context.fetch=async()=>({ok:false,status:404,json:async()=>{throw new SyntaxError('not JSON');}});
  vm.runInContext(apiSource,context);
  await assert.rejects(context.api('/api/save',{}),e=>e.name==='SyntaxError'&&e.status===undefined);
  await context.finishSession();assert.equal(lost.hidden,true);assert.equal(answer.value,'synthetic answer');assert.equal(alerts.length,1);assert.deepEqual(shown,[]);
});
