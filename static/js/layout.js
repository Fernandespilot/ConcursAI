/* ConcursAI — shared sidebar layout */
(function(){
  const API = 'http://localhost:8000';
  const NAV = [
    { section: 'Principal' },
    { href:'/pages/home',        icon:'fa-home',          label:'Início',      key:'home'        },
    { href:'/pages/dashboard',   icon:'fa-chart-bar',     label:'Dashboard',   key:'dashboard'   },
    { section: 'IA & Busca' },
    { href:'/pages/chat',        icon:'fa-comments',      label:'Chat IA',     key:'chat'        },
    { href:'/pages/concursos',   icon:'fa-search',        label:'Concursos',   key:'concursos'   },
    { href:'/pages/ferramentas', icon:'fa-magic',         label:'Ferramentas', key:'ferramentas' },
    { section: 'Documentos' },
    { href:'/pages/edital',      icon:'fa-file-pdf',      label:'Edital',      key:'edital'      },
    { href:'/pages/provas',      icon:'fa-file-alt',      label:'Provas',      key:'provas'      },
    { section: 'Sistema' },
    { href:'/pages/scraping',    icon:'fa-spider',        label:'Scraping',    key:'scraping'    },
    { href:'/pages/admin',       icon:'fa-shield-alt',    label:'Admin',       key:'admin'       },
  ];

  function buildSidebar(activeKey){
    const links = NAV.map(n => {
      if(n.section) return `<div class="sidebar-section">${n.section}</div>`;
      const active = n.key === activeKey ? ' active' : '';
      return `<a href="${n.href}" class="nav-link${active}"><i class="fas ${n.icon}"></i>${n.label}</a>`;
    }).join('');

    return `
<aside class="sidebar">
  <a href="/pages/home" class="sidebar-brand">
    <div class="brand-icon"><i class="fas fa-graduation-cap"></i></div>
    ConcursAI
  </a>
  ${links}
  <div class="sidebar-footer">
    <div class="status-pill" style="justify-content:center;padding:8px 10px;background:none;border:none">
      <span class="status-dot" id="g-sdot"></span>
      <span id="g-stxt" style="font-size:.72rem;color:var(--text-3)">verificando...</span>
    </div>
  </div>
</aside>`;
  }

  function buildTopbar(breadcrumb){
    const right = `
      <div class="topbar-right">
        <a href="/pages/dashboard" class="btn btn-secondary btn-sm" style="font-size:.72rem">
          <i class="fas fa-chart-bar"></i> Dashboard
        </a>
        <a href="http://localhost:8000/docs" target="_blank" class="btn btn-secondary btn-sm" style="font-size:.72rem">
          <i class="fas fa-code"></i> API
        </a>
      </div>`;
    return `
<div class="topbar">
  <div class="topbar-left">${breadcrumb}</div>
  ${right}
</div>`;
  }

  async function checkStatus(){
    try {
      await fetch(API+'/status', {signal: AbortSignal.timeout(3000)});
      document.getElementById('g-sdot').className = 'status-dot online';
      document.getElementById('g-stxt').textContent = 'Online';
    } catch(e) {
      document.getElementById('g-sdot').className = 'status-dot offline';
      document.getElementById('g-stxt').textContent = 'Offline';
    }
  }

  window.initLayout = function(opts){
    // opts = { active, title, breadcrumb }
    const active = opts.active || '';
    const breadcrumb = opts.breadcrumb ||
      `<a href="/pages/home">Início</a><span class="sep">/</span><span class="current">${opts.title||active}</span>`;

    // Inject sidebar before body content
    const sidebarEl = document.createElement('div');
    sidebarEl.innerHTML = buildSidebar(active);
    document.body.insertBefore(sidebarEl.firstElementChild, document.body.firstChild);

    // Wrap everything after sidebar in .main-wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'main-wrapper';

    // Insert topbar
    wrapper.innerHTML = buildTopbar(breadcrumb);

    // Move all remaining body children into wrapper
    const children = Array.from(document.body.children).filter(el => !el.classList.contains('sidebar'));
    children.forEach(el => wrapper.appendChild(el));

    document.body.appendChild(wrapper);

    checkStatus();
  };
})();
