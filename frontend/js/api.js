const API_BASE = window.location.origin;

const api = {
  getToken(){ return localStorage.getItem('sm_token') },
  setToken(t){ localStorage.setItem('sm_token', t) },
  getUser(){ try{ return JSON.parse(localStorage.getItem('sm_user')||'null') }catch{ return null } },
  setUser(u){ localStorage.setItem('sm_user', JSON.stringify(u)) },
  clearAuth(){ localStorage.removeItem('sm_token'); localStorage.removeItem('sm_user') },

  async request(path, opts={}){
    const headers = { ...(opts.headers||{}) };
    const token = this.getToken();
    if(token) headers['Authorization'] = `Bearer ${token}`;
    if(!(opts.body instanceof FormData)){
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }
    const res = await fetch(`${API_BASE}${path}`, {...opts, headers});
    let data;
    try{ data = await res.json() }catch{ data = {} }
    if(res.status === 401){
      this.clearAuth();
      if(!window.location.pathname.includes('login') && !window.location.pathname.includes('register')){
        window.location.href = '/login.html';
      }
      throw new Error(data.detail || 'Session expired');
    }
    if(!res.ok) throw new Error(data.detail || data.error || 'Request failed');
    return data;
  },

  get(path){ return this.request(path) },
  post(path, body){ return this.request(path,{method:'POST',body:JSON.stringify(body)}) },
  put(path, body){ return this.request(path,{method:'PUT',body:JSON.stringify(body)}) },
  delete(path){ return this.request(path,{method:'DELETE'}) },
  postForm(path, fd){ return this.request(path,{method:'POST',body:fd,headers:{}}) },
};

function requireAuth(){
  if(!api.getToken()){ window.location.href='/login.html'; return false; }
  return true;
}

function showToast(msg, type='success', duration=3500){
  let c = document.querySelector('.toast-container');
  if(!c){ c=document.createElement('div'); c.className='toast-container'; document.body.appendChild(c); }
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${msg}</span>`;
  c.appendChild(t);
  setTimeout(()=>{ t.style.opacity='0'; t.style.transform='translateX(40px)'; t.style.transition='all .3s'; setTimeout(()=>t.remove(),300); }, duration);
}

function formatDate(d){
  if(!d) return '';
  return new Date(d).toLocaleDateString('en-US',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
}

function formatRelative(d){
  if(!d) return '';
  const diff = Date.now() - new Date(d).getTime();
  const m = Math.floor(diff/60000);
  if(m < 1) return 'just now';
  if(m < 60) return `${m}m ago`;
  const h = Math.floor(m/60);
  if(h < 24) return `${h}h ago`;
  return `${Math.floor(h/24)}d ago`;
}

function initSidebar(activePage){
  const user = api.getUser();
  const nav = [
    {href:'/dashboard.html', icon:'📊', label:'Dashboard'},
    {href:'/chat.html',      icon:'💬', label:'AI Chat'},
    {href:'/notes.html',     icon:'📝', label:'Notes'},
    {href:'/quiz.html',      icon:'❓', label:'Quiz'},
    {href:'/flashcards.html',icon:'🃏', label:'Flashcards'},
    {href:'/analytics.html', icon:'📈', label:'Analytics'},
    {href:'/settings.html',  icon:'⚙️', label:'Settings'},
  ];
  const sb = document.querySelector('.sidebar');
  if(!sb) return;
  sb.innerHTML = `
    <div class="sidebar-logo">
      <div class="logo-icon">🎓</div>
      <span>StudyMate AI</span>
    </div>
    <ul class="nav-links">
      ${nav.map(n=>`<li><a href="${n.href}" class="${activePage===n.href?'active':''}"><span class="nav-icon">${n.icon}</span>${n.label}</a></li>`).join('')}
    </ul>
    <div class="sidebar-user">
      <div class="user-name">👤 ${user?.name||'Student'}</div>
      <button class="btn btn-ghost btn-sm w-full" onclick="logout()">🚪 Logout</button>
    </div>`;

  // Mobile toggle
  let mBtn = document.querySelector('.mobile-btn');
  if(!mBtn){
    mBtn = document.createElement('button');
    mBtn.className = 'mobile-btn';
    mBtn.innerHTML = '☰';
    document.body.appendChild(mBtn);
  }
  mBtn.onclick = ()=>{ sb.classList.toggle('open'); };
  document.addEventListener('click', e=>{ if(!sb.contains(e.target)&&!mBtn.contains(e.target)) sb.classList.remove('open'); });
}

function logout(){ api.clearAuth(); window.location.href='/login.html'; }

function initReveal(){
  const obs = new IntersectionObserver(entries=>{
    entries.forEach(e=>{ if(e.isIntersecting) e.target.classList.add('visible'); });
  },{threshold:.08});
  document.querySelectorAll('.reveal').forEach(el=>obs.observe(el));
}

function initParticles(){
  const c = document.querySelector('.particles');
  if(!c) return;
  for(let i=0;i<18;i++){
    const p=document.createElement('div'); p.className='particle';
    p.style.cssText=`left:${Math.random()*100}%;top:${Math.random()*100}%;animation-delay:${Math.random()*6}s;animation-duration:${4+Math.random()*5}s`;
    c.appendChild(p);
  }
}

document.addEventListener('DOMContentLoaded',()=>{ initReveal(); initParticles(); });
