const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
function setup(){
  const source=fs.readFileSync(path.join(__dirname,'../product/index.html'),'utf8').match(/async function finishSession\([^]*?\n}/)[0];
  const answer={value:'synthetic answer'};const shown=[];const alerts=[];
  const context=vm.createContext({state:{sessionId:'synthetic',exportData:{stale:true}},document:{getElementById:()=>answer},show:id=>shown.push(id),alert:m=>alerts.push(m)});
  vm.runInContext(source,context);return {context,answer,shown,alerts};
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
