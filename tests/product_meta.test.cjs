const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');

test('CSV participant names and date metadata are escaped as text in upload summary',()=>{
  const nodes=new Map();
  const get=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',children:[],appendChild(n){this.children.push(n);}});return nodes.get(id);};
  const document={getElementById:get,createElement:()=>({set textContent(value){this.text=String(value);},get innerHTML(){return this.text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}})};
  const context=vm.createContext({document});
  const html=fs.readFileSync(path.join(__dirname,'../product/index.html'),'utf8');
  for(const name of ['renderMeta','esc']){
    const source=html.match(new RegExp('function '+name+'\\([^]*?\\n}'));
    assert.ok(source,'function '+name+' found');vm.runInContext(source[0],context);
  }
  const payload='<img src=x onerror="globalThis.injected=true">';
  context.renderMeta({meta:{total_messages:2,me:payload,me_messages:1,partner:payload,other_messages:1,start_date:payload,end_date:payload,total_days:1},users:[{name:payload,count:1}],detected_me:payload});
  const markup=get('metaCard').innerHTML;
  assert.equal(markup.includes('<img'),false);
  assert.equal((markup.match(/&lt;img/g)||[]).length,4);
  assert.match(markup,/총 메시지/);assert.match(markup,/2건/);
  const option=get('meSelect').children[0];
  assert.equal(option.value,payload);assert.equal(option.text,payload+' (1건)');assert.equal(option.selected,true);
});
