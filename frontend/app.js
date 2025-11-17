const API_BASE = 'http://127.0.0.1:5003';

const { useState, useEffect, useRef, useMemo } = React;


function classNames(...a){ return a.filter(Boolean).join(' '); }

function formatNumberOrDate(v){
  if (typeof v === 'number' && Number.isFinite(v)) return new Intl.NumberFormat().format(v);
  if (typeof v === 'string' && /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(v)) { const d = new Date(v); if (!isNaN(d)) return d.toLocaleString(); }
  return v;
}

function shortModelName(model){
  if(!model) return '';
  try{
    const m = String(model);
    const slash = m.lastIndexOf('/');
    const name = slash >= 0 ? m.slice(slash+1) : m;
    return name.length > 28 ? name.slice(0,25) + '…' : name;
  }catch{ return String(model); }
}

function normalizeEnvelope(data){
  const type = data && data.type ? String(data.type) : null;
  const llm_model = (data && (data.llm_model || data.llmModel)) || null;
  const answer_source = (data && (data.answer_source || data.answerSource)) || null;
  const trace_id = (data && (data.trace_id || data.traceId)) || null;
  const result = (data && data.result) || null;
  const error  = (data && data.error)  || null;
  return { type, llm_model, answer_source, trace_id, result, error, full: data };
}


function isFlatUniformArray(arr){
  if (!Array.isArray(arr) || arr.length === 0) return false;
  const first = arr[0];
  if (typeof first !== 'object' || first === null || Array.isArray(first)) return false;
  const keys = Object.keys(first).sort();
  return arr.every(it => {
    if (typeof it !== 'object' || it === null || Array.isArray(it)) return false;
    const k = Object.keys(it).sort();
    return k.length === keys.length && k.every((ki,i)=>ki===keys[i]);
  });
}

// Utility to classify primitive values for styling
function getValueTypeClass(v){
  if (v === null) return 'null';
  const t = typeof v;
  if (t === 'string') return 'string';
  if (t === 'number') return 'number';
  if (t === 'boolean') return 'boolean';
  return '';
}

function renderBasicMarkdown(text){
  if (!text) return '';
  let html = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  html = html
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/^\s*[-•] (.+)$/gm,'<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs,'<ul>$1<\/ul>');
  return html;
}

function JsonViewerPanel({ dataEnvelope }){
  const [search, setSearch] = useState('');
  const [viewMode, setViewMode] = useState('tree');
  const [visibleCount, setVisibleCount] = useState(100);
  const [itemsPerChunk, setItemsPerChunk] = useState(100);
  const [expanded, setExpanded] = useState(new Set());
  const [maxDepth, setMaxDepth] = useState(10);

  const payload = dataEnvelope?.result?.payload;
  const schema = dataEnvelope?.result?.schema;

  const canTable = useMemo(()=>isFlatUniformArray(payload),[payload]);
  useEffect(()=>{
    setViewMode('tree');
    setVisibleCount(100);
    setSearch('');
    setMaxDepth(10);
    // Initialize expansion: root expanded; if root is array, expand first item recursively
    function collectExpandablePaths(node, pathArr, nodeSchema){
      const paths = [];
      const isExpandable = Array.isArray(node) || (node && typeof node === 'object');
      if (isExpandable) {
        paths.push(pathKey(pathArr));
        if (Array.isArray(node)) {
          // expand all children of this item
          node.forEach((child, idx) => {
            const childPath = pathArr.concat(idx + 1);
            paths.push(...collectExpandablePaths(child, childPath, nodeSchema && nodeSchema.items));
          });
        } else if (node && typeof node === 'object') {
          Object.keys(node).forEach(k => {
            const childPath = pathArr.concat(k);
            const nextSchema = nodeSchema && nodeSchema.properties && nodeSchema.properties[k];
            paths.push(...collectExpandablePaths(node[k], childPath, nextSchema));
          });
        }
      }
      return paths;
    }
    const init = new Set([ 'root' ]);
    if (Array.isArray(payload) && payload.length > 0) {
      // expand first item recursively
      const firstItemPaths = collectExpandablePaths(payload[0], ['1'], schema && schema.items);
      firstItemPaths.forEach(p => init.add(p));
    }
    setExpanded(init);
  },[payload, schema]);

  // Auto expand/collapse based on search filter: expand nodes containing matches; collapse others
  useEffect(() => {
    if (!payload) return;
    if (!search) return; // leave initial expansion logic when filter is empty

    const expandedKeys = new Set(['root']);

    function hasMatchValue(val) {
      try {
        if (typeof val === 'object' && val !== null) {
          return JSON.stringify(val).toLowerCase().includes(search.toLowerCase());
        }
        return String(val).toLowerCase().includes(search.toLowerCase());
      } catch { return String(val).toLowerCase().includes(search.toLowerCase()); }
    }

    function walk(node, pathArr, currentSchema) {
      // returns true if subtree contains a match
      if (Array.isArray(node)) {
        let any = false;
        node.forEach((child, idx) => {
          const childPath = pathArr.concat(idx + 1);
          const childHas = walk(child, childPath, currentSchema && currentSchema.items);
          if (childHas) {
            any = true;
            expandedKeys.add(pathKey(pathArr)); // open this array
            expandedKeys.add(pathKey(childPath)); // open the matching child container if it has children
          }
        });
        return any;
      }
      if (node && typeof node === 'object') {
        let any = false;
        const props = Object.entries(node);
        for (const [k, v] of props) {
          const matchesHere = matchesSearch(k, v) || hasMatchValue(v);
          const childPath = pathArr.concat(k);
          if (v && typeof v === 'object') {
            const childSchema = currentSchema && currentSchema.properties && currentSchema.properties[k];
            const childHas = walk(v, childPath, childSchema);
            if (childHas) {
              any = true;
              expandedKeys.add(pathKey(pathArr));
              expandedKeys.add(pathKey(childPath));
              continue;
            }
          }
          if (matchesHere) {
            any = true;
            expandedKeys.add(pathKey(pathArr));
          }
        }
        return any;
      }
      // primitive
      return hasMatchValue(node);
    }

    walk(payload, [], schema);
    setExpanded(expandedKeys);
  }, [search, payload, schema]);

  // Determine chunk size based on viewport height (3x window height chunk)
  useEffect(() => {
    const ROW_PX = 28; // approximate per-row height
    function recalc() {
      const chunk = Math.max(50, Math.ceil((window.innerHeight * 3) / ROW_PX));
      setItemsPerChunk(chunk);
      if (Array.isArray(payload)) {
        setVisibleCount(Math.min(payload.length, chunk));
      }
    }
    recalc();
    window.addEventListener('resize', recalc);
    return () => window.removeEventListener('resize', recalc);
  }, [payload]);

  // Schema helpers for titles
  const getPropertyTitle = (objSchema, key) => {
    const title = objSchema && objSchema.properties && objSchema.properties[key] && objSchema.properties[key].title;
    return (typeof title === 'string' && title.trim()) ? title : null;
  };
  const getSchemaTitle = sch => (sch && typeof sch.title === 'string' && sch.title.trim()) ? sch.title : null;
  const getItemsSchema = sch => (sch && sch.items) ? sch.items : null;
  const getObjectProperties = sch => (sch && sch.properties) ? sch.properties : null;
  const getLabelForKey = (key, objSchema) => getPropertyTitle(objSchema, key) || key;

  function renderLeafRow(keyLabel, value, depth){
    const typeClass = getValueTypeClass(value);
    const display = formatNumberOrDate(value);
    return React.createElement('div', { className: 'json-row json-leaf', style: { marginLeft: depth * 14 } },
      React.createElement('span', { className: 'json-key' }, keyLabel + ':'),
      React.createElement('span', { className: `json-value ${typeClass}` }, ' ' + String(display))
    );
  }

  function matchesSearch(key, value){
    if (!search) return true;
    const s = search.toLowerCase();
    try{
      if (String(key).toLowerCase().includes(s)) return true;
      if (typeof value === 'object') return JSON.stringify(value).toLowerCase().includes(s);
      return String(value).toLowerCase().includes(s);
    }catch{ return String(value).toLowerCase().includes(s); }
  }

  function copyAll(){ try{ navigator.clipboard.writeText(JSON.stringify(payload,null,2)); }catch{} }
  function copyNode(node){ try{ navigator.clipboard.writeText(JSON.stringify(node,null,2)); }catch{} }
  function exportJson(){ try{ const b=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}); const u=URL.createObjectURL(b); const a=document.createElement('a'); a.href=u; a.download='data.json'; a.click(); URL.revokeObjectURL(u);}catch{} }
  function exportCsvIfTabular(){ if(!canTable) return; const rows=payload; const headers=Object.keys(rows[0]); const itemSchema = getItemsSchema(schema) || {}; const titled=headers.map(h=> getPropertyTitle(itemSchema, h) || h ); const esc=v=>`"${(v==null?'':String(v)).replace(/"/g,'""')}"`; const csv=[titled.join(',')].concat(rows.map(r=>headers.map(h=>esc(r[h])).join(','))).join('\n'); const b=new Blob([csv],{type:'text/csv'}); const u=URL.createObjectURL(b); const a=document.createElement('a'); a.href=u; a.download='data.csv'; a.click(); URL.revokeObjectURL(u);}

  const pathKey = path => ['root'].concat(path).join('.');
  const togglePath = path => setExpanded(prev=>{ const next=new Set(prev); const key=pathKey(path); if(next.has(key)) next.delete(key); else next.add(key); return next; });

  function renderTree(value, depth=0, path=[], currentSchema=schema){
    if (depth >= maxDepth) {
      return React.createElement('div',{className:'json-hint'}, React.createElement('button',{className:'btn', onClick:()=>setMaxDepth(d=>d+5)},'Expand deeper (+5)'));
    }
    if (Array.isArray(value)){
      const key = pathKey(path);
      const isOpen = expanded.has(key);
      const rootTitle = depth===0 ? (getSchemaTitle(currentSchema) || getLabelForKey(path[path.length-1]??'[]', currentSchema)) : getLabelForKey(path[path.length-1]??'[]', currentSchema);
      const header = React.createElement('div',{className:'json-row hoverable json-array', style:{fontWeight:600,display:'flex',alignItems:'center',gap:6, marginLeft: depth * 14}, onClick:()=>togglePath(path)},
        React.createElement('span',{className:'json-toggle'}, isOpen?'▾':'▸'),
        React.createElement('span',null,`${rootTitle}`)
      );
      const itemSchema = getItemsSchema(currentSchema) || null;
      const singular = getSchemaTitle(itemSchema) || null;
      const children = isOpen ? value.slice(0, visibleCount).map((item, idx)=>{
        const indexOne = idx+1;
        const childPath = path.concat(indexOne);
        const childKey = pathKey(childPath);
        const itemOpen = expanded.has(childKey);
        const label = (singular || 'Item') + ' ' + indexOne + ':';
        const itemHeader = React.createElement('div', { className: 'json-row hoverable json-object', style: { fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6, marginLeft: (depth + 1) * 14 }, onClick: () => togglePath(childPath) },
          React.createElement('span', { className: 'json-toggle' }, itemOpen ? '▾' : '▸'),
          React.createElement('span', { className: 'json-title' }, label)
        );
        const itemChildren = itemOpen ? renderTree(item, depth + 1, childPath, itemSchema) : null;
        return React.createElement('div', { key: indexOne }, itemHeader, itemChildren);
      }) : null;
      const showMore = isOpen && value.length>visibleCount ? React.createElement('button',{className:'btn', onClick:()=>setVisibleCount(c=>Math.min(value.length, c + itemsPerChunk))},'Show more') : null;
      return React.createElement('div', null, header, children, showMore);
    } else if (value && typeof value === 'object'){
      const propsSchema = getObjectProperties(currentSchema) || {};
      return Object.entries(value).filter(([k,v])=>matchesSearch(k,v)).map(([k,v])=>{
        const childPath = path.concat(k);
        const key = pathKey(childPath);
        const isOpen = expanded.has(key);
        const nextSchema = propsSchema && propsSchema[k] ? propsSchema[k] : null;
        const keyLabel = getLabelForKey(k, currentSchema);
        if (v === null || typeof v !== 'object') {
          return React.createElement('div', { key: k }, renderLeafRow(keyLabel, v, depth + 1));
        }
        const header = React.createElement('div',{ className:'json-row hoverable json-object', style:{fontWeight:600,display:'flex',alignItems:'center',gap:6, marginLeft: depth * 14}, onClick:()=>togglePath(childPath)},
          React.createElement('span',{className:'json-toggle'}, isOpen?'▾':'▸'),
          React.createElement('span',null,keyLabel)
        );
        const children = isOpen ? renderTree(v, depth+1, childPath, nextSchema) : null;
        return React.createElement('div',{key:k}, header, children);
      });
    } else {
      // Primitive node: indent one level deeper than its parent container
      return renderLeafRow('(value)', value, depth + 1);
    }
  }

  if (!payload){
    return React.createElement('div',{className:'panel-inner json-viewer-container'}, React.createElement('div',{className:'json-hint'},'No data yet'));
  }
  if (typeof payload === 'string'){
    return React.createElement('div',{className:'panel-inner json-viewer-container'}, React.createElement('div',{className:'json-hint'},'Invalid data'));
  }

  const toolbar = React.createElement('div',{className:'json-toolbar'},
    React.createElement('input',{type:'text',placeholder:'Search keys and values…',value:search,onChange:e=>setSearch(e.target.value)}),
    isFlatUniformArray(payload) ? React.createElement('button',{className:'btn',onClick:()=>setViewMode(m=>m==='table'?'tree':'table')}, viewMode==='table'?'Tree view':'Table view') : null,
    viewMode==='table' && isFlatUniformArray(payload) ? React.createElement('button',{className:'btn',onClick:exportCsvIfTabular},'Export .csv') : null
  );

  let content = null;
  if (viewMode==='table' && isFlatUniformArray(payload)){
    const rows = payload.slice(0, visibleCount);
    const headers = Object.keys(payload[0]);
    const itemSchema = getItemsSchema(schema) || {};
    content = React.createElement('div',{className:'json-scroll'},
      React.createElement('table',{style:{width:'100%',borderCollapse:'collapse'}},
        React.createElement('thead',null,
          React.createElement('tr',null,
            React.createElement('th',{style:{textAlign:'left',padding:'8px',borderBottom:'1px solid #e5e7eb'}},'#'),
            headers.map(h=>React.createElement('th',{key:h,style:{textAlign:'left',padding:'8px',borderBottom:'1px solid #e5e7eb'}}, getPropertyTitle(itemSchema, h) || h))
          )
        ),
        React.createElement('tbody',null,
          rows.filter(r=>matchesSearch('', r)).map((row, idx)=>
            React.createElement('tr',{key:idx},
              React.createElement('td',{style:{padding:'8px',borderBottom:'1px solid #f3f4f6',color:'#6b7280'}}, idx+1),
              headers.map(h=>{
                const val = row[h];
                const typeClass = getValueTypeClass(val);
                return React.createElement('td',{key:h,style:{padding:'8px',borderBottom:'1px solid #f3f4f6'}, onDoubleClick:()=>copyNode(val)},
                  React.createElement('span',{className:`json-value ${typeClass}`}, String(formatNumberOrDate(val)))
                );
              })
            )
          )
        )
      )
    );
  } else {
    content = React.createElement('div',{className:'json-scroll'}, renderTree(payload, 0, [], schema));
  }

  const showMore = Array.isArray(payload) && payload.length>visibleCount ? React.createElement('button',{className:'btn',onClick:()=>setVisibleCount(c=>c+200)},'Show more') : null;

  return React.createElement('div',{className:'panel-inner json-viewer-container'}, toolbar, content, showMore);
}

function ChatPanel({ onSend, messages, loading }){
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const [recognizing, setRecognizing] = useState(false);
  const recognitionRef = useRef(null);
  const [notice, setNotice] = useState('');

  useEffect(()=>{ messagesEndRef.current?.scrollIntoView({behavior:'smooth'}); },[messages,loading]);


  useEffect(()=>{
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition){ setNotice('Voice unavailable. You can still type.'); return; }
    const rec = new SpeechRecognition(); rec.continuous=false; rec.interimResults=false; rec.lang='en';
    rec.onresult = e => { const t = Array.from(e.results).map(r=>r[0].transcript).join(' '); setInput(p=> (p? p+' ' : '') + t); };
    rec.onerror = () => { setNotice('Voice unavailable. You can still type.'); setRecognizing(false); };
    rec.onend = () => setRecognizing(false);
    recognitionRef.current = rec;
  },[]);

  function detectLang(text){ if(/[\u0400-\u04FF]/.test(text)) return 'ru'; if(/ä|ö|ü|ß|Ä|Ö|Ü/.test(text)) return 'de'; return 'en'; }
  function startVoice(){ const rec=recognitionRef.current; if(!rec){ setNotice('Voice unavailable. You can still type.'); return; } rec.lang = detectLang(input||''); try{ rec.start(); setRecognizing(true);}catch{} }
  function stopVoice(){ try{ recognitionRef.current?.stop(); }catch{} }

  async function handleSend(){ const text=input.trim(); if(!text) return; if(text.length>2000) return; setInput(''); onSend(text); }
  function onKeyDown(e){ if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); handleSend(); } }

  return React.createElement('div',{className:'panel-inner chat-container'},
    React.createElement('div',{className:'messages'},
      messages.map((m, idx) => {
        const isErrorEnvelope = m.envelopeType === 'error' || m.isError;
        const msgClass = classNames(
          'msg',
          m.role,
          isErrorEnvelope && 'error',
          !isErrorEnvelope && m.source === 'llm' && 'source-llm',
          !isErrorEnvelope && m.source === 'backend' && 'source-backend'
        );

        return React.createElement('div', {
          key: idx,
          className: msgClass,
          ['data-testid']: `msg-${idx}-${m.role}`
        }, [
          (m.role === 'assistant' && m.source === 'llm')
            ? React.createElement('div', { className: 'msg-label' }, `LLM${(m.envelopeType !== 'error' && m.llmModel) ? ' · ' + shortModelName(m.llmModel) : ''}`)
            : (m.role === 'assistant' && m.source === 'backend')
            ? React.createElement('div', { className: 'msg-label' }, 'backend')
            : (m.role === 'user')
            ? React.createElement('div', { className: classNames('msg-label', 'right') }, 'you')
            : null,
          React.createElement('div', {
            className: 'msg-content',
            dangerouslySetInnerHTML: { __html: renderBasicMarkdown(m.content) }
          })
        ]);
      }),
      loading ? React.createElement('div',{className:'msg system'},'Assistant is thinking…') : null,
      React.createElement('div',{ref:messagesEndRef})
    ),
    React.createElement('div',{className:'chat-input'},
      React.createElement('textarea',{value:input,placeholder:'Type a message…',onChange:e=>setInput(e.target.value),onKeyDown}),
      React.createElement('button',{className:'btn secondary',onClick:recognizing?stopVoice:startVoice}, recognizing?'Stop':'Voice'),
      React.createElement('button',{className:'btn',onClick:handleSend},'Send')
    ),
    notice ? React.createElement('div',{className:'chat-hint'}, notice) : null,
    React.createElement('div',{className:'chat-hint'}, 'Enter to send • Shift+Enter for newline')
  );
}

function Modal({ open, title, message, onClose }){
  return React.createElement('div',{className:classNames('modal-backdrop', open&&'show')},
    React.createElement('div',{className:'modal'},
      React.createElement('h3',null,title),
      React.createElement('p',null,message),
      React.createElement('div',{style:{marginTop:12,textAlign:'right'}}, React.createElement('button',{className:'btn',onClick:onClose},'Close'))
    )
  );
}

function App(){
  const [messages,setMessages] = useState([]);
  const [dataEnvelope,setDataEnvelope] = useState(null);
  const [loading,setLoading] = useState(false);
  const [modal,setModal] = useState({open:false,title:'',message:''});

function addMessage(role, content, isError = false, source = null, llmModel = null, traceId = null, envelopeType = null) {
  setMessages(prev => [...prev, { role, content, isError, source, llmModel, traceId, envelopeType }]);
}

async function sendToApi(userText) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000);
  setLoading(true);
  addMessage('user', userText);
  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_input: userText }),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    // If the response is not OK, it might be a structured error from our backend.
    if (!res.ok) {
      let data;
      try {
        data = await res.json();
      } catch (e) {
        // The response was not valid JSON (e.g., a gateway error with HTML).
        // We throw to trigger the modal for these kinds of network/proxy errors.
        const errText = res.status >= 500 || res.status === 0 ? 'backend_unavailable' : 'internal_error';
        throw new Error(errText);
      }

      // If we successfully parsed JSON, we can now check if it's our error format.
      if (data) {
        const env = normalizeEnvelope(data);
        // If it's a structured error, handle it here and exit the function.
        // This prevents it from falling through to the generic `catch` block.
        if (env.type === 'error') {
          handleErrorEnvelope(env);
          return; // Exit successfully after handling the chat message.
        }
      }

      // If we are here, it means res was not .ok and it was either not JSON
      // or not a structured error envelope. We throw to trigger the modal.
      throw new Error('internal_error');
    }

    const data = await res.json();
    const env = normalizeEnvelope(data);

    if (!env || !env.type) {
      addMessage('assistant', 'Unknown response format from server', true);
      return;
    }

    switch (env.type) { case 'error': { handleErrorEnvelope(env); break; }

      case 'text': {
        const msg = (env.result && (env.result.message || env.result.text || env.result.content))
          || data.message
          || 'Received empty response from model.';
        const rawSource = env.answer_source ? String(env.answer_source).toLowerCase() : null;
        addMessage('assistant', msg, false, rawSource, env.llm_model || null, env.trace_id || null);
        break;
      }

      case 'data': {
        setDataEnvelope(env.full);
        const note = (env.result && env.result.message)
          ? env.result.message
          : 'Received structured data.';
        const rawSource = env.answer_source ? String(env.answer_source).toLowerCase() : null;
        addMessage('assistant', note, false, rawSource, env.llm_model || null, env.trace_id || null);
        break;
      }

      default: {
        addMessage('assistant', `Unsupported response type: ${String(env.type)}`, true, env.answer_source || null, env.llm_model || null, env.trace_id || null);
      }
    }
  } catch (err) {
    // This block will now only be reached for network errors, timeouts,
    // or non-JSON server errors, which is what we want for the modal.
    clearTimeout(timeoutId);

    console.error('Request to backend failed:', err);

    const errMsg = err && typeof err.message === 'string' ? err.message : '';

    let title = 'Request error';
    let message = 'There was an error or timeout. Please re-enter your message in chat.';

    // 1) Timeout via AbortController → dedicated message
    if (err && err.name === 'AbortError') {
      title = 'Backend timeout';
      message = 'The request to the backend timed out. Please check if the backend server is running and reachable.';
    }
    // 2) Explicit backend_unavailable marker or typical fetch TypeError (network unreachable)
    else if (errMsg === 'backend_unavailable' || err instanceof TypeError) {
      title = 'Backend unavailable';
      message = 'Backend server is not running or unreachable.';
    }
    // 3) Known logical errors that we explicitly throw
    else if (errMsg === '`user_input` is required' || errMsg === 'Content-Type must be application/json') {
      // Keep the generic title, but refine the message text
      message = errMsg;
    }
    // 4) Internal backend error while the server is running
    else if (errMsg === 'internal_error') {
      title = 'Backend error';
      message = 'The backend responded with an internal error. Please check the backend logs for details.';
    }
    // 5) In all other cases, keep the default "Request error"

    setModal({
      open: true,
      title,
      message,
    });

    // Mirror the same information in the chat as an assistant error message
    addMessage('assistant', message, true, 'backend', null, null, 'error');
  } finally {
    setLoading(false);
  }
}

function handleErrorEnvelope(env) {
  const traceIdStr = env.trace_id ? `Trace ID: ${env.trace_id}` : 'Trace ID: unavailable';
  const llmModel = env.llm_model || null;

  // This is a structured error from the backend, like the 503 "model overloaded".
  // We prioritize the `error.message` field which is more machine-readable.
  if (env.error && env.error.message) {
    const errorCode = env.error.code != null ? env.error.code : 'N/A';
    const message = env.error.message || 'No message provided.';
    const traceId = env.trace_id || 'N/A';
    const llmModelStr = env.llm_model || 'N/A';
    const errorMessage = `Error Code: ${errorCode}\nMessage: ${message}\nTrace ID: ${traceId}\nLLM Model: ${llmModelStr}`;
    addMessage(
      'assistant',
      errorMessage,
      true,
      env.answer_source || 'backend',
      llmModel,
      env.trace_id,
      'error'
    );
  }
  // Fallback for other kinds of structured 'error' type envelopes
  else if (env.result && env.result.message) {
    const rawSource = env.answer_source ? String(env.answer_source).toLowerCase() : 'backend';
    addMessage('assistant', env.result.message, true, rawSource, llmModel, env.trace_id, 'error');
  }
  // Generic fallback if the error envelope is malformed
  else {
    addMessage('assistant', 'An unknown application error occurred.', true, 'backend', llmModel, env.trace_id, 'error');
  }
}

  return React.createElement('div',{className:'app'},
    React.createElement('header',{className:'header'}, React.createElement('h1',{className:'header-title'},'Apartment Manager')),
    React.createElement('main',{className:'content'},
      React.createElement('section',{className:'panel'}, React.createElement(JsonViewerPanel,{dataEnvelope})),
      React.createElement('section',{className:'panel'}, React.createElement(ChatPanel,{onSend:sendToApi,messages,loading}))
    ),
    React.createElement(Modal,{open:modal.open,title:modal.title,message:modal.message,onClose:()=>setModal(m=>({...m,open:false}))})
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(React.createElement(App));