// Run with Node.js: node tests/check_task_display.cjs (no packages required).
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Element {
  constructor(tag){this.tag=tag;this.children=[];this.textContent='';}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this.children=nodes;}
  showModal(){this.open=true;}
}
const nodes={};
const context=vm.createContext({document:{createElement:t=>new Element(t),querySelector:s=>nodes[s]??=(new Element('div'))},console});
const code=fs.readFileSync('bridge/static/app.js','utf8');
vm.runInContext(code.slice(code.indexOf('const $='),code.indexOf('let config='))+code.slice(code.indexOf('function node('),code.indexOf('function message('))+code.slice(code.indexOf('const detailLabels='),code.indexOf('function formatted(')),context);
vm.runInContext(`let draft=null;const analysisLanguage='en';const analysis={source_language:'Chinese',summary:'Test registration.',actions:[{title:'Test registration',steps:['Create account','Verify email','Log in'],conditions:'None',location:'Computer lab',deadline_text:'October 5, 2–3 p.m.',source_quote:'原文'}],missing_information:['None'],words:[]};renderAnalysis();openTask(analysis.actions[0]);`,context);
function all(n){return [n,...n.children.flatMap(all)];}
const rendered=all(nodes['#result']);
assert.equal(rendered.filter(n=>n.tag==='button'&&n.textContent==='Track this task').length,1);
assert.equal(rendered.filter(n=>n.tag==='li').length,3);
assert(!rendered.some(n=>n.textContent==='None'));
assert(rendered.some(n=>n.textContent==='Where: Computer lab'));
assert.equal(all(nodes['#draft-condition']).filter(n=>n.tag==='li').length,3);
assert(nodes['#task-dialog'].open);
console.log('Task display checks passed: one card, three steps, optional fields, and task review.');
