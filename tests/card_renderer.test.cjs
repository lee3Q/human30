const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');

// A text-only DOM double: any attempt to parse HTML or inline handlers fails.
class Element {
  constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this.style={};this.events={};this.value='';this.classList={add(){},remove(){}};}
  set innerHTML(value){throw new Error('HTML parsing is forbidden for imported seed data');}
  setAttribute(name,value){if(name.startsWith('on'))throw new Error('inline handler');this[name]=value;}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this.children=nodes;}
  addEventListener(name,fn){this.events[name]=fn;}
}
function setup(){
  const nodes=new Map();
  const document={createElement:tag=>new Element(tag),getElementById:id=>{
    if(!nodes.has(id))nodes.set(id,new Element('div'));return nodes.get(id);
  }};
  const context=vm.createContext({document,alert:message=>{throw new Error(message);}});
  context.window=context;
  const html=fs.readFileSync(path.join(__dirname,'../scripts/card_renderer.html'),'utf8');
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],context);
  return {context,nodes};
}
const walk=node=>[node,...node.children.flatMap(walk)];
const texts=node=>walk(node).map(n=>n.textContent).filter(x=>x!==undefined);
const fixture=()=>JSON.parse(fs.readFileSync(path.join(__dirname,'../runs/seed_001.json'),'utf8'));

test('all included cards, filters, reset, and detail JSON remain usable',()=>{
  const {context,nodes}=setup();const seed=fixture();context.loadSeed(seed);
  assert.equal(nodes.get('grid').children.length,30);
  nodes.get('filterSex').value='M';nodes.get('filterSex').events.change();
  assert.equal(nodes.get('grid').children.length,seed.characters.filter(c=>c.sex==='M').length);
  nodes.get('resetBtn').events.click();assert.equal(nodes.get('grid').children.length,30);
  const button=walk(nodes.get('grid')).find(n=>n.tagName==='button');
  button.events.click();assert.deepEqual(JSON.parse(nodes.get('modalContent').textContent),seed.characters[0]);
  nodes.get('expandAll').events.click();assert.deepEqual(JSON.parse(nodes.get('modalContent').textContent),seed);
});

test('imported labels, attributes, IDs, ages and seed stay literal text/data',()=>{
  const {context,nodes}=setup();const seed=fixture();seed.characters=seed.characters.slice(0,1);
  const payload='<img src=x onerror="globalThis.injected=true">';
  const c=seed.characters[0];c.id='1);globalThis.injected=true;//';c.age=payload;c.sex='" onmouseover="injected=true';
  c.body.height_cm=payload;c.memory.trauma=payload;c.post_hoc_label=[payload,'<svg onload="injected=true">'];seed.seed=payload;
  context.loadSeed(seed);
  const grid=nodes.get('grid');assert.equal(grid.children.length,1);
  assert.ok(texts(grid).includes(payload));assert.ok(texts(grid).includes(c.id));
  assert.equal(walk(grid).filter(n=>n.tagName==='img'||n.tagName==='svg').length,0);
  assert.equal(context.injected,undefined);
  walk(grid).find(n=>n.tagName==='button').events.click();
  assert.deepEqual(JSON.parse(nodes.get('modalContent').textContent),c);
  nodes.get('filterSex').value='M';nodes.get('filterSex').events.change();
  assert.ok(texts(grid).includes('해당 조건의 캐릭터가 없습니다'));
});


test('failed import preserves cards, stats, filters and last good JSON source',()=>{
  const {context,nodes}=setup();const good=fixture();context.loadSeed(good);
  nodes.get('filterSex').value='M';nodes.get('filterSex').events.change();
  const cards=nodes.get('grid').children;const stats=nodes.get('stats').textContent;
  for(const invalid of [null,{}, {characters:[null]}, ...['bmi','labels','secret'].map(kind=>{
    const seed=fixture();seed.seed='rejected';
    if(kind==='bmi')seed.characters[0].body.body_composition.bmi='bad';
    if(kind==='labels')seed.characters[0].post_hoc_label={length:1};
    if(kind==='secret')seed.characters[0].memory.secret={length:40};
    return seed;
  })]){
    assert.throws(()=>context.loadSeed(invalid));
    assert.equal(nodes.get('grid').children,cards);
    assert.equal(nodes.get('stats').textContent,stats);
    assert.equal(nodes.get('filterSex').value,'M');
    nodes.get('expandAll').events.click();
    assert.deepEqual(JSON.parse(nodes.get('modalContent').textContent),good);
  }
  const replacement=fixture();replacement.seed=0;context.loadSeed(replacement);
  assert.match(nodes.get('stats').textContent,/시드 0/);
  assert.equal(nodes.get('modalContent').textContent,'');
  nodes.get('resetBtn').events.click();assert.equal(nodes.get('grid').children.length,30);
});
