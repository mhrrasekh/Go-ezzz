const modelOptions = [
  {id:'openai',name:'OpenAI · GPT',subtitle:'Official account or API access',badge:'Account-dependent',badgeType:'conditional',icon:'◎',iconClass:'openai',description:'Use GPT only through an official OpenAI product or an authorized API integration. Free availability and usage limits depend on your account and current plan.',steps:['Check the free features available to your OpenAI account.','For an API integration, review current pricing and usage limits before enabling it.','Never put an API key in this static website; use a secure backend for live connections.'],url:'https://openai.com/'},
  {id:'claude',name:'Anthropic · Claude',subtitle:'Official account or API access',badge:'Account-dependent',badgeType:'conditional',icon:'✳',iconClass:'claude',description:'Claude access is governed by Anthropic account, plan, region, and usage limits. This app cannot create free access or remove those limits.',steps:['Check the Claude plan and usage available to your account.','Treat API usage as paid unless your account explicitly provides a free allowance.','Use secure server-side integration for any future live connection.'],url:'https://claude.ai/'},
  {id:'ollama',name:'Ollama · Local models',subtitle:'Run compatible open models on your computer',badge:'No per-token API fee',badgeType:'local-only',icon:'⌘',iconClass:'local',description:'Run supported open-weight models locally. There is no per-token provider API charge, but hardware, electricity, storage, and model licenses still matter.',steps:['Install Ollama for your operating system.','Choose a model that fits your available RAM and hardware.','A future local connector can call the Ollama service on your own device.'],url:'https://ollama.com/'},
  {id:'gemini',name:'Google · Gemini',subtitle:'Check current developer free tier',badge:'Tier-dependent',badgeType:'conditional',icon:'✦',iconClass:'router',description:'Google may offer free-tier access to selected Gemini models and developer services, subject to current model, region, and rate limits.',steps:['Review current model availability and free-tier terms.','Check data-use terms before sending sensitive information.','Configure a connector only after verifying the current quota and restrictions.'],url:'https://ai.google.dev/'},
  {id:'openrouter',name:'OpenRouter · Free models',subtitle:'Browse models marked free',badge:'Model-dependent',badgeType:'conditional',icon:'⇄',iconClass:'router',description:'Some models may be offered with free routing and can have strict rate limits, availability changes, or provider-specific terms.',steps:['Inspect which models are currently marked free.','Read provider-specific rate limits and data policies.','Expect free model availability and capacity to change.'],url:'https://openrouter.ai/models'},
  {id:'local',name:'Other local runtimes',subtitle:'Self-hosted inference options',badge:'Hardware-dependent',badgeType:'local-only',icon:'▧',iconClass:'local',description:'Other local runtimes can provide a no-per-token-cost inference route when you have suitable hardware and comply with each model license.',steps:['Choose a runtime compatible with your operating system and hardware.','Check the model license and minimum memory requirements.','Connect through a local-only adapter in a future release.'],url:'https://github.com/ggml-org/llama.cpp'}
];
const $ = (selector) => document.querySelector(selector);
const modelList = $('#model-list');
const dialog = $('#model-dialog');
const dialogContent = $('#dialog-content');
function renderModels(){
  modelList.innerHTML = modelOptions.slice(0,4).map(m=>`<button class="model-row" type="button" data-model="${m.id}" aria-label="Setup guidance for ${m.name}"><span class="provider-icon ${m.iconClass}">${m.icon}</span><span class="model-info"><strong>${m.name}</strong><small>${m.subtitle}</small></span><span class="availability ${m.badgeType}">${m.badge}</span><span class="row-arrow">›</span></button>`).join('');
  modelList.querySelectorAll('[data-model]').forEach(button=>button.addEventListener('click',()=>showModel(button.dataset.model)));
}
function showModel(id){
  const model=modelOptions.find(item=>item.id===id); if(!model)return;
  dialogContent.innerHTML=`<div class="dialog-symbol ${model.iconClass}">${model.icon}</div><div class="eyebrow">CONNECTION GUIDE</div><h2>${model.name}</h2><p>${model.description}</p><ul>${model.steps.map(step=>`<li>${step}</li>`).join('')}</ul><div class="dialog-note">Status: guidance only. This preview does not verify your account, quota, or live connectivity.</div><a class="dialog-link" href="${model.url}" target="_blank" rel="noreferrer">Open official resource ↗</a>`;
  dialog.showModal();
}
function readSettings(){
  try{return JSON.parse(localStorage.getItem('freeai-hub-settings')||'{}')}catch{return {}}
}
function applySettings(settings){
  $('#routing-mode').value=settings.routingMode||'free-first';
  $('#fallback-toggle').checked=settings.fallback!==false;
  $('#paid-toggle').checked=settings.blockPaid!==false;
  $('#stat-routing').textContent={ 'free-first':'Free-first',quality:'Quality-first','local-first':'Local-first',manual:'Manual'}[$('#routing-mode').value]||'Free-first';
}
function saveSettings(){
  const settings={routingMode:$('#routing-mode').value,fallback:$('#fallback-toggle').checked,blockPaid:$('#paid-toggle').checked};
  try{localStorage.setItem('freeai-hub-settings',JSON.stringify(settings));applySettings(settings);$('#save-status').textContent='Preferences saved on this device.';}
  catch{$('#save-status').textContent='Could not save locally. Check browser storage settings.';}
}
function navigate(view,link){
  document.querySelectorAll('.nav-link').forEach(item=>item.classList.toggle('active',item===link));
  const titles={home:'Overview',models:'Model catalog',routing:'Smart routing',providers:'Providers'};
  $('#breadcrumb-current').textContent=titles[view]||'Overview';
  if(view==='models'){$('#model-list').scrollIntoView({behavior:'smooth',block:'center'});}
  else if(view==='routing'){$('#routing-panel').scrollIntoView({behavior:'smooth',block:'center'});}
  else if(view==='providers'){showModel('openai');}
  else{window.scrollTo({top:0,behavior:'smooth'});}
}
document.querySelectorAll('[data-view]').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();navigate(link.dataset.view,link);}));
$('#save-settings').addEventListener('click',saveSettings);
$('#routing-mode').addEventListener('change',()=>{$('#save-status').textContent='Unsaved changes';});
$('#fallback-toggle').addEventListener('change',()=>{$('#save-status').textContent='Unsaved changes';});
$('#paid-toggle').addEventListener('change',()=>{$('#save-status').textContent='Unsaved changes';});
$('.notice-close').addEventListener('click',()=>$('.notice').remove());
dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close();});
renderModels();
applySettings(readSettings());
