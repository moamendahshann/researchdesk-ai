const $ = id => document.getElementById(id);
let latest = null;
function status(text) { $('status').textContent = text; }
async function api(path, options={}) {
 const response = await fetch(path, options);
 let data; try { data = await response.json(); } catch { throw Error('Server returned an unreadable response.'); }
 if (!response.ok) throw Error(typeof data.detail==='string' ? data.detail : 'Request failed. Please check your input.');
 return data;
}
async function refresh() {
 const docs = await api('/api/documents');
 const selected=$('scope').value;
 $('documents').replaceChildren(); $('scope').replaceChildren(new Option('All documents','')); $('count').textContent=docs.length;
 for (const doc of docs) {
  const row=document.createElement('div');row.className='document';
  const detail=document.createElement('div'), name=document.createElement('strong'), meta=document.createElement('small');
  name.textContent=doc.name;meta.textContent=`${doc.pages} pages${doc.empty_pages ? ' · '+doc.empty_pages+' pages without text':''}`;detail.append(name,meta);
  const del=document.createElement('button');del.textContent='×';del.setAttribute('aria-label','Delete '+doc.name);
  del.onclick=async()=>{if(!confirm('Delete this PDF and clear saved question history?'))return;try{await api('/api/documents/'+doc.id,{method:'DELETE'});latest=null;$('result').hidden=true;$('history').hidden=true;await refresh();status('Document deleted. Saved history cleared.');}catch(e){status(e.message);}};
  row.append(detail,del);$('documents').append(row);$('scope').add(new Option(doc.name,doc.id));
 }
 if(docs.some(d=>d.id===selected))$('scope').value=selected;
}
$('upload').onchange=async event=>{
 const files=[...event.target.files]; $('ask').disabled=true;
 for(const file of files){
  status('Indexing '+file.name+'…');
  try{if(file.size>10*1024*1024)throw Error('Maximum file size is 10 MB.');const r=await api('/api/documents?name='+encodeURIComponent(file.name),{method:'POST',headers:{'Content-Type':'application/pdf'},body:file});status(r.duplicate?'Already in your library.':`Added ${file.name}${r.empty_pages ? '. Some pages have no extractable text.':''}`);await refresh();}catch(e){status(file.name+': '+e.message);break;}
 }
 event.target.value='';$('ask').disabled=false;
};
function show(result){
 latest=result;$('result').hidden=false;$('history').hidden=true;$('answer').textContent=result.answer;$('warning').textContent=result.warning;
 $('result-title').textContent=result.mode==='generated'?'AI synthesis':'Evidence found';$('sources').replaceChildren();
 result.sources.forEach((source,i)=>{
  const card=document.createElement('article');card.className='source';
  const link=document.createElement('a');link.href='/api/documents/'+encodeURIComponent(source.document_id)+'/pdf#page='+source.page;link.target='_blank';link.rel='noopener';link.textContent=`[${i+1}] ${source.name} · Page ${source.page} ↗`;
  const text=document.createElement('p');text.dir='auto';text.textContent=source.text;
  const score=document.createElement('small');score.textContent='Lexical similarity: '+source.score+' · not a confidence probability';card.append(link,text,score);$('sources').append(card);
 });status(result.sources.length+' passages · '+result.elapsed_ms+' ms');
}
$('search-form').onsubmit=async event=>{
 event.preventDefault();$('ask').disabled=true;status('Finding evidence…');
 try{const result=await api('/api/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:$('question').value,document_id:$('scope').value||null,generate:$('generate').checked})});show(result);}catch(e){status(e.message);}finally{$('ask').disabled=false;}
};
$('history-toggle').onclick=async()=>{try{const rows=await api('/api/history');$('history').hidden=false;$('history-list').replaceChildren();for(const row of rows){const button=document.createElement('button');button.className='history-item';button.textContent=row.query;button.onclick=()=>show(JSON.parse(row.result));$('history-list').append(button);}if(!rows.length)$('history-list').textContent='No saved questions yet.';}catch(e){status(e.message);}};
$('clear-history').onclick=async()=>{try{await api('/api/history',{method:'DELETE'});$('history-list').textContent='History cleared.';}catch(e){status(e.message);}};
$('export').onclick=()=>{if(!latest)return;let text='# Research notes\n\n'+latest.question+'\n\n'+latest.answer+'\n\n'+latest.warning+'\n\n';latest.sources.forEach((s,i)=>{text+=`## [${i+1}] ${s.name}, page ${s.page}\n\n${s.text}\n\n`;});const url=URL.createObjectURL(new Blob([text],{type:'text/markdown;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='research-notes.md';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
(async()=>{try{await refresh();const config=await api('/api/status');$('generate').disabled=!config.generation_available;$('ai-status').textContent=config.generation_available?'Optional external provider':'Provider not configured';}catch(e){status(e.message);}})();
