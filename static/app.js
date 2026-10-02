/* ═══════════════════════════════════════════════════════════
   VocGuide - Main Application JavaScript
   AI Career Counselling Platform
═══════════════════════════════════════════════════════════ */

const API = (typeof window !== 'undefined' && window.location && window.location.origin && window.location.origin.startsWith('http'))
  ? `${window.location.origin}/api`
  : 'http://localhost:5000/api';

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ── State ──────────────────────────────────────────────────
const state = {
  language: 'en',
  chatLang: 'en',
  sessionId: null,
  trades: [],
  filteredTrades: [],
  activeSector: 'all',
  isTyping: false,
  recognition: null,
  isRecording: false,
  adminData: null,
  authToken: localStorage.getItem('vg_token') || null,
  currentUser: JSON.parse(localStorage.getItem('vg_user') || 'null'),
  mediaRecorder: null,
  isVoiceRecording: false,
  voiceChunks: [],
};

// ── i18n strings ───────────────────────────────────────────
const i18n = {
  en: {
    navHome: 'Home',
    navTrades: 'Explore Trades',
    navCounsellor: 'Career Guidance',
    navAdmin: 'Admin Dashboard',
    navCta: 'Start Guidance',
    heroBadge: 'Trusted Career Guidance • For Indian Families',
    heroTitle: "Your Family's Guide to",
    heroSub: "Simple career guidance for students and parents, with verified facts on salaries, workplace safety, and career growth for every ITI trade.",
    heroCta1: 'Talk to Counsellor',
    heroCta2: 'Explore Trades',
    stat1: 'Verified Trades',
    stat2: 'Placement Rate',
    stat3: 'Languages',
    stat4: 'Top Earnings/Month',
    featTitle: 'Why VocGuide?',
    featSub: 'Designed for Indian families, backed by verified facts',
    cpTitle: 'Setup Your Guidance Session',
    cpSub: 'Tell us a little about yourself for tailored guidance',
    startSession: 'Start Guidance',
    sendHint: 'Press Enter to send • Shift+Enter for new line',
    welcomeMsg: "Namaste! Welcome to VocGuide, your advisor for vocational training and ITI courses.",
    typingText: 'VocGuide is writing an answer...',
    qqTitle: 'Frequently Asked Questions',
    escTitle: 'Talk to a Senior Counsellor',
    escDesc: 'Our experienced vocational advisors are available to assist with detailed queries. An advisor will contact you within 24 hours.',
    escSubmit: 'Request Free Call',
    sentimentLabel: 'Discussion status:',
    aiStatus: 'Ready to help your family',
    quickQs: [
      'What are the best paying trades?',
      'Is electrician work safe for my child?',
      'What government schemes are available?',
      'Can women enroll in beauty & wellness trade?',
      'What is the NSQF qualification pathway?',
      'How much can a plumber earn in 5 years?',
    ]
  },
  hi: {
    navHome: 'होम',
    navTrades: 'ट्रेड खोजें',
    navCounsellor: 'करियर मार्गदर्शन',
    navAdmin: 'एडमिन डैशबोर्ड',
    navCta: 'मार्गदर्शन शुरू करें',
    heroBadge: 'भरोसेमंद करियर मार्गदर्शन • विद्यार्थियों और परिवारों के लिए',
    heroTitle: 'व्यावसायिक सफलता के लिए',
    heroSub: 'विद्यार्थियों और अभिभावकों के लिए एक सरल मंच, जहाँ ITI ट्रेडों की वास्तविक कमाई, सुरक्षा और भविष्य की स्पष्ट जानकारी मिलती है।',
    heroCta1: 'मार्गदर्शन प्राप्त करें',
    heroCta2: 'ट्रेड देखें',
    stat1: 'सत्यापित ट्रेड',
    stat2: 'प्लेसमेंट दर',
    stat3: 'भाषाएं',
    stat4: 'अधिकतम कमाई/माह',
    featTitle: 'VocGuide क्यों?',
    featSub: 'भारतीय परिवारों के लिए सरल, सत्यापित डेटा से संचालित',
    cpTitle: 'सत्र विवरण भरें',
    cpSub: 'उचित सलाह के लिए कृपया कुछ जानकारी साझा करें',
    startSession: 'मार्गदर्शन शुरू करें',
    sendHint: 'भेजने के लिए Enter दबाएं • नई लाइन के लिए Shift+Enter',
    welcomeMsg: 'नमस्ते! वोकगाइड में आपका स्वागत है, व्यावसायिक शिक्षा और ITI ट्रेड के लिए आपका मार्गदर्शक।',
    typingText: 'वोकगाइड उत्तर तैयार कर रहा है...',
    qqTitle: 'अक्सर पूछे जाने वाले प्रश्न',
    escTitle: 'वरिष्ठ काउंसलर से बात करें',
    escDesc: 'हमारे अनुभवी करियर सलाहकार आपकी सहायता के लिए उपलब्ध हैं। 24 घंटे में आपसे संपर्क किया जाएगा।',
    escSubmit: 'मुफ्त कॉलबैक अनुरोध करें',
    sentimentLabel: 'बातचीत का माहौल:',
    aiStatus: 'आपके परिवार की मदद के लिए तैयार',
    quickQs: [
      'सबसे ज्यादा कमाई वाले ट्रेड कौन से हैं?',
      'क्या इलेक्ट्रीशियन का काम सुरक्षित है?',
      'कौन सी सरकारी योजनाएं उपलब्ध हैं?',
      'क्या बेटियां ब्यूटी ट्रेड कर सकती हैं?',
      'NSQF योग्यता मार्ग क्या है?',
      'प्लम्बर 5 साल में कितना कमा सकता है?',
    ]
  }
};

const ADVISOR_AVATAR = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>`;
const USER_AVATAR = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;
const DEFAULT_TRADE_ICON = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`;

const TRADE_ICONS = {
  electrician: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
  plumber: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`,
  beauty_wellness: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/><line x1="8.12" y1="8.12" x2="12" y2="12"/></svg>`,
  computer_operator: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`,
  welder: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>`,
  healthcare_assistant: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`,
  sewing_technology: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/><line x1="8.12" y1="8.12" x2="12" y2="12"/></svg>`,
  automobile_service: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>`
};

const CONCERN_ICONS = { income: '•', safety: '•', social_status: '•', career_growth: '•', female_safety: '•' };
const CONCERN_COLORS = { income: '#f59e0b', safety: '#ef4444', social_status: '#6366f1', career_growth: '#10b981', female_safety: '#ec4899' };

// ══════════════════════════════════════════════════════════
// NAVIGATION
// ══════════════════════════════════════════════════════════
function showSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

  const sec = document.getElementById(name);
  if (sec) sec.classList.add('active');

  const link = document.querySelector(`.nav-link[href="#${name}"]`);
  if (link) link.classList.add('active');

  // Lazy load sections
  if (name === 'trades' && state.trades.length === 0) loadTrades();
  if (name === 'admin') checkAdminAccess();
  if (name === 'counsellor') populateTradeSelector();

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ══════════════════════════════════════════════════════════
// LANGUAGE
// ══════════════════════════════════════════════════════════
function setLanguage(lang) {
  state.language = lang;
  state.chatLang = lang;
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`lang-${lang}`)?.classList.add('active');

  document.querySelectorAll('.lt-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`lt-${lang}`)?.classList.add('active');

  document.querySelectorAll('.colt-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`colt-${lang}`)?.classList.add('active');

  applyTranslations();
}

async function setChatLang(lang) {
  if (lang !== 'en' && lang !== 'hi') lang = 'en';
  state.chatLang = lang;

  document.querySelectorAll('.lt-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`lt-${lang}`)?.classList.add('active');

  document.querySelectorAll('.colt-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`colt-${lang}`)?.classList.add('active');

  if (state.sessionId && !state.sessionId.startsWith('local-')) {
    try {
      fetch(`${API}/chat/set-language`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: state.sessionId, language: lang })
      });
    } catch (e) {
      console.warn('Language sync error:', e);
    }
  }

  populateQuickQuestions();

  const langLabel = lang === 'hi' ? 'हिन्दी (Hindi)' : 'English';
  showToast(`Response language set to ${langLabel}. You can ask in English, Hindi, or Hinglish!`, 'info');
}

function applyTranslations() {
  const t = i18n[state.language] || i18n.en;
  const set = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };

  set('nav-cta-text', t.navCta);
  set('badge-text', t.heroBadge);
  set('hero-subtitle', t.heroSub);
  set('stat-1', t.stat1);
  set('stat-2', t.stat2);
  set('stat-3', t.stat3);
  set('stat-4', t.stat4);
  set('features-title', t.featTitle);
  set('features-subtitle', t.featSub);
  set('cp-title', t.cpTitle);
  set('cp-subtitle', t.cpSub);
  set('start-session-text', t.startSession);
  set('input-hint', t.sendHint);
  set('typing-text', t.typingText);
  set('qq-title', t.qqTitle);
  set('esc-title', t.escTitle);
  set('esc-desc', t.escDesc);
  set('esc-submit-text', t.escSubmit);
  set('sentiment-label', t.sentimentLabel);
  set('ai-status-text', t.aiStatus);

  populateQuickQuestions();
}

function populateQuickQuestions() {
  const t = i18n[state.chatLang] || i18n.en;
  const container = document.getElementById('qq-chips');
  if (!container) return;
  container.innerHTML = t.quickQs.map(q =>
    `<button class="qq-chip" onclick="sendQuickQuestion(this.textContent)">${q}</button>`
  ).join('');
}

// ══════════════════════════════════════════════════════════
// TRADES EXPLORER
// ══════════════════════════════════════════════════════════
async function loadTrades() {
  const grid = document.getElementById('trades-grid');
  if (!grid) return;

  try {
    const res = await fetch(`${API}/trades`);
    state.trades = await res.json();
    state.filteredTrades = [...state.trades];
    renderTrades();
    populateTradeSelector();
  } catch (e) {
    grid.innerHTML = `<div class="empty-state"><div class="empty-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></div><p>Could not load trade data. Make sure the server is running.</p></div>`;
  }
}

function renderTrades() {
  const grid = document.getElementById('trades-grid');
  if (!grid) return;

  if (state.filteredTrades.length === 0) {
    grid.innerHTML = `<div class="empty-state"><p>No trades found matching your search.</p></div>`;
    return;
  }

  grid.innerHTML = state.filteredTrades.map(t => `
    <div class="trade-card" onclick="openTradeModal('${t.id}')" tabindex="0">
      <div class="tc-header">
        <div class="tc-icon">${TRADE_ICONS[t.id] || DEFAULT_TRADE_ICON}</div>
        <div class="tc-badge">NSQF ${t.nsqf_level}</div>
      </div>
      <div class="tc-name">${state.language === 'hi' ? t.name_hi : t.name}</div>
      <div class="tc-sector">${state.language === 'hi' ? t.sector_hi : t.sector}</div>
      <div class="tc-metrics">
        <div class="tc-metric">
          <div class="tc-metric-val">₹${(t.avg_experienced_salary/1000).toFixed(0)}K</div>
          <div class="tc-metric-label">Avg Monthly</div>
        </div>
        <div class="tc-metric">
          <div class="tc-metric-val">₹${(t.top_salary/1000).toFixed(0)}K</div>
          <div class="tc-metric-label">Top Earners</div>
        </div>
        <div class="tc-metric">
          <div class="tc-metric-val">${t.job_growth_percent}%</div>
          <div class="tc-metric-label">Job Growth</div>
        </div>
        <div class="tc-metric">
          <div class="tc-metric-val">${t.duration_months}mo</div>
          <div class="tc-metric-label">Duration</div>
        </div>
      </div>
      <div class="tc-placement-bar">
        <div class="tc-bar-label">
          <span>Placement Rate</span>
          <span>${t.placement_rate}%</span>
        </div>
        <div class="tc-bar-track">
          <div class="tc-bar-fill" style="width:0%" data-width="${t.placement_rate}%"></div>
        </div>
      </div>
      <div class="tc-footer">
        <span class="tc-duration">Self-employ: ${t.self_employment_potential}</span>
        <button class="tc-btn" onclick="event.stopPropagation(); startCounsellingFor('${t.id}')">
          Counsel Me
        </button>
      </div>
    </div>
  `).join('');

  // Animate bars after render
  requestAnimationFrame(() => {
    document.querySelectorAll('.tc-bar-fill[data-width]').forEach(bar => {
      setTimeout(() => { bar.style.width = bar.dataset.width; }, 100);
    });
  });
}

function filterTrades() {
  const search = document.getElementById('trade-search')?.value.toLowerCase() || '';
  const sort = document.getElementById('trade-sort')?.value || 'placement';

  state.filteredTrades = state.trades.filter(t => {
    const matchName = t.name.toLowerCase().includes(search) || t.sector.toLowerCase().includes(search);
    if (state.activeSector === 'all') return matchName;
    if (state.activeSector === 'construction') return matchName && t.sector.toLowerCase().includes('construction');
    if (state.activeSector === 'it') return matchName && t.sector.toLowerCase().includes('information');
    if (state.activeSector === 'healthcare') return matchName && t.sector.toLowerCase().includes('health');
    if (state.activeSector === 'beauty') return matchName && t.sector.toLowerCase().includes('beauty');
    if (state.activeSector === 'automotive') return matchName && t.sector.toLowerCase().includes('auto');
    return matchName;
  });

  sortTrades();
}

function sortTrades() {
  const sort = document.getElementById('trade-sort')?.value || 'placement';
  state.filteredTrades.sort((a, b) => {
    if (sort === 'placement') return b.placement_rate - a.placement_rate;
    if (sort === 'salary') return b.avg_experienced_salary - a.avg_experienced_salary;
    if (sort === 'growth') return b.job_growth_percent - a.job_growth_percent;
    return 0;
  });
  renderTrades();
}

function filterBySector(sector, btn) {
  state.activeSector = sector;
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  filterTrades();
}

function populateTradeSelector() {
  const sel = document.getElementById('trade-interest');
  if (!sel || sel.options.length > 1) return; // already populated

  if (state.trades.length === 0) {
    fetch(`${API}/trades`).then(r => r.json()).then(trades => {
      state.trades = trades;
      doPopulate(sel, trades);
    }).catch(() => {});
  } else {
    doPopulate(sel, state.trades);
  }
}

function doPopulate(sel, trades) {
  trades.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.id;
    opt.textContent = t.name;
    sel.appendChild(opt);
  });
}

// Trade Detail Modal
async function openTradeModal(tradeId) {
  const overlay = document.getElementById('trade-modal');
  const content = document.getElementById('trade-modal-content');

  overlay.style.display = 'flex';
  content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><span>Loading...</span></div>';

  try {
    const res = await fetch(`${API}/trades/${tradeId}`);
    const t = await res.json();
    renderTradeModal(t);
  } catch (e) {
    const t = state.trades.find(tr => tr.id === tradeId);
    if (t) renderTradeModal(t);
  }
}

function renderTradeModal(t) {
  const content = document.getElementById('trade-modal-content');
  const concernMap = {
    income: { icon: '•', label: 'Income' },
    safety: { icon: '•', label: 'Safety' },
    social_status: { icon: '•', label: 'Social Status' },
    growth: { icon: '•', label: 'Career Growth' },
    female_safety: { icon: '•', label: 'Women Safety' }
  };

  content.innerHTML = `
    <div class="modal-hero">
      <div class="modal-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg></div>
      <div class="modal-title-group">
        <h2>${t.name}</h2>
        <div class="modal-sub">${t.sector} • NSQF Level ${t.nsqf_level} • ${t.duration_months} months</div>
      </div>
      <button class="modal-close-btn" onclick="closeTradeModal()"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button>
    </div>
    <div class="modal-body-inner">
      <div class="modal-metrics-grid">
        <div class="modal-metric">
          <div class="mm-val">₹${t.avg_starting_salary.toLocaleString()}</div>
          <div class="mm-label">Starting Salary</div>
        </div>
        <div class="modal-metric">
          <div class="mm-val">₹${t.avg_experienced_salary.toLocaleString()}</div>
          <div class="mm-label">Avg (3-5 yrs)</div>
        </div>
        <div class="modal-metric">
          <div class="mm-val">₹${t.top_salary.toLocaleString()}</div>
          <div class="mm-label">Top Earners</div>
        </div>
        <div class="modal-metric">
          <div class="mm-val">${t.placement_rate}%</div>
          <div class="mm-label">Placement Rate</div>
        </div>
        <div class="modal-metric">
          <div class="mm-val">${t.job_growth_percent}%</div>
          <div class="mm-label">Job Growth/yr</div>
        </div>
        <div class="modal-metric">
          <div class="mm-val">${t.self_employment_potential}</div>
          <div class="mm-label">Self-Employment</div>
        </div>
      </div>

      <div class="modal-section">
        <h3>Career Progression (NSQF Pathway)</h3>
        <div class="career-path">
          ${t.career_progression.map((step, i) => `
            <div class="career-step">
              <div class="cs-level">${step.level}</div>
              <div class="cs-role">${step.role}</div>
              <div class="cs-years">${step.years} yrs</div>
              <div class="cs-salary">₹${step.salary}/mo</div>
            </div>
          `).join('<div style="text-align:center;color:var(--primary-light);font-size:18px;padding:4px">↓</div>')}
        </div>
      </div>

      <div class="modal-section">
        <h3>Common Parent Concerns and Answers</h3>
        <div class="parental-concerns">
          ${Object.entries(t.parental_concerns_addressed).map(([key, val]) => `
            <div class="concern-item">
              <div class="concern-icon">${concernMap[key]?.icon || '•'}</div>
              <div class="concern-text"><strong>${concernMap[key]?.label || key}:</strong> ${val}</div>
            </div>
          `).join('')}
        </div>
      </div>

      <div class="modal-section">
        <h3>Top Employers</h3>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          ${t.top_employers.map(emp => `<span style="padding:6px 14px;background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.2);border-radius:20px;font-size:13px;">${emp}</span>`).join('')}
        </div>
      </div>

      <div class="modal-section">
        <h3>Certifications &amp; Qualifications</h3>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          ${t.certifications.map(cert => `<span style="padding:6px 14px;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);border-radius:20px;font-size:13px;">${cert}</span>`).join('')}
        </div>
      </div>

      <div class="modal-actions">
        <button class="btn-primary" onclick="closeTradeModal(); startCounsellingFor('${t.id}')">
          Ask Questions about ${t.name}
        </button>
        <button class="btn-secondary" onclick="closeTradeModal()">Close</button>
      </div>
    </div>
  `;
}

function closeTradeModal(event) {
  if (!event || event.target === document.getElementById('trade-modal')) {
    document.getElementById('trade-modal').style.display = 'none';
  }
}

function startCounsellingFor(tradeId) {
  document.getElementById('trade-interest').value = tradeId;
  showSection('counsellor');
}

// ══════════════════════════════════════════════════════════
// CAREER COUNSELLOR
// ══════════════════════════════════════════════════════════
async function startSession() {
  const name = document.getElementById('learner-name')?.value;
  const location = document.getElementById('learner-location')?.value;
  const education = document.getElementById('learner-education')?.value;
  const income = document.getElementById('family-income')?.value;
  const trade = document.getElementById('trade-interest')?.value;
  const concern = document.getElementById('parent-concern')?.value;

  try {
    const res = await fetch(`${API}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        learner_name: name,
        location,
        education,
        family_income: income,
        trade_id: trade || null,
        parent_concerned: concern,
        language: state.chatLang
      })
    });
    const data = await res.json();
    state.sessionId = data.session_id;

    // Auto-send greeting based on context
    const greeting = buildGreeting(name, trade, concern);
    if (greeting) {
      setTimeout(() => sendMessage(greeting), 500);
    }
    showToast('Session started. Start chatting below.', 'success');
  } catch (e) {
    // Still allow chatting without session
    state.sessionId = 'local-' + Date.now();
    showToast('Offline mode: responses use local data.', 'error');
  }
}

function buildGreeting(name, trade, concern) {
  const lang = state.chatLang;
  if (lang === 'hi') {
    if (name && trade && concern) return `नमस्ते, मेरा नाम ${name} है। मैं ${trade} ट्रेड में रुचि रखता/रखती हूं। हमारे परिवार को ${concern} के बारे में चिंता है। कृपया मदद करें।`;
    if (name) return `नमस्ते, मेरा नाम ${name} है। कृपया मुझे व्यावसायिक प्रशिक्षण के बारे में जानकारी दें।`;
    return null;
  } else {
    if (name && trade && concern) return `Hello, my name is ${name}. I'm interested in the ${trade} trade. My family has concerns about ${concern}. Please help us make a decision.`;
    if (name) return `Hello, I'm ${name}. Can you guide us on vocational training options?`;
    return null;
  }
}

async function sendMessage(text) {
  const input = document.getElementById('chat-input');
  const message = text || input?.value.trim();
  if (!message || state.isTyping) return;

  if (!text && input) input.value = '';
  if (input) autoResize(input);

  // Show user message
  appendMessage(message, 'user');

  // Show typing
  setTyping(true);

  try {
    const res = await fetch(`${API}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: state.sessionId,
        message,
        language: state.chatLang,
        trade_id: document.getElementById('trade-interest')?.value || null,
        learner_name: document.getElementById('learner-name')?.value || null,
        location: document.getElementById('learner-location')?.value || null,
        family_income: document.getElementById('family-income')?.value || null,
        education: document.getElementById('learner-education')?.value || null,
        parent_concerned: document.getElementById('parent-concern')?.value || null
      })
    });

    const data = await res.json();
    setTyping(false);

    if (!res.ok || !data.response) {
      const errMsg = data.error || (state.chatLang === 'hi'
        ? 'क्षमा करें, उत्तर तैयार करने में समस्या आई। कृपया पुनः प्रयास करें।'
        : 'Sorry, unable to prepare the response right now. Please try again.');
      appendMessage(errMsg, 'ai');
      return;
    }

    if (!state.sessionId && data.session_id) state.sessionId = data.session_id;

    if (data.learner_name) {
      const nameInput = document.getElementById('learner-name');
      if (nameInput && !nameInput.value) nameInput.value = data.learner_name;
    }
    if (data.trade_id) {
      const tradeSelect = document.getElementById('trade-interest');
      if (tradeSelect && (!tradeSelect.value || tradeSelect.value === '')) tradeSelect.value = data.trade_id;
    }
    if (data.speaker_title) {
      const statusText = document.getElementById('ai-status-text');
      if (statusText) {
        statusText.innerHTML = `Speaking with: <strong>${escapeHtml(data.speaker_title)}</strong>`;
      }
    }

    appendMessage(data.response, 'ai');
    updateSentiment(data.sentiment);

    if (data.suggest_escalation) {
      setTimeout(() => showEscalationSuggestion(), 1000);
    }
  } catch (e) {
    console.error('Chat dispatch error:', e);
    setTyping(false);
    const fallback = state.chatLang === 'hi'
      ? 'क्षमा करें, परामर्श सेवा से संपर्क नहीं हो पाया। कृपया सुनिश्चित करें कि सर्वर चालू है।'
      : 'Unable to connect to the guidance service right now. Please make sure the server is running on port 5000.';
    appendMessage(fallback, 'ai');
  }
}

function appendMessage(text, role) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `chat-message ${role}-message`;

  const avatar = role === 'ai' ? ADVISOR_AVATAR : USER_AVATAR;
  const now = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });

  // Format text: convert markdown-ish to HTML
  const html = formatMessageText(text);

  div.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-content">
      <div class="msg-bubble">${html}</div>
      <div class="msg-time">${now}</div>
    </div>
  `;

  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function formatMessageText(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)+/g, match => `<ul>${match}</ul>`)
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[ul|li|p])(.+)$/gm, '<p>$1</p>')
    .replace(/<p><\/p>/g, '');
}

function setTyping(active) {
  state.isTyping = active;
  const indicator = document.getElementById('typing-indicator');
  const sendBtn = document.getElementById('send-btn');

  if (indicator) indicator.classList.toggle('active', active);
  if (sendBtn) sendBtn.disabled = active;

  if (active) {
    document.getElementById('chat-messages')?.scrollTo({ top: 99999, behavior: 'smooth' });
  }
}

function updateSentiment(sentiment) {
  const badge = document.getElementById('sentiment-badge');
  if (!badge) return;

  const labels = {
    positive: state.chatLang === 'hi' ? 'सकारात्मक' : 'Positive',
    neutral: state.chatLang === 'hi' ? 'तटस्थ' : 'Neutral',
    concerned: state.chatLang === 'hi' ? 'चिंतित' : 'Concerned'
  };

  badge.textContent = labels[sentiment] || sentiment;
  badge.className = `sentiment-badge ${sentiment}`;
}

function showEscalationSuggestion() {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-message ai-message';
  div.innerHTML = `
    <div class="msg-avatar">${ADVISOR_AVATAR}</div>
    <div class="msg-content">
      <div class="msg-bubble" style="border-color:rgba(245,158,11,0.3);background:rgba(245,158,11,0.05)">
        <p>Would you like to speak directly with an experienced <strong>vocational advisor</strong>?</p>
        <button class="btn-secondary" onclick="showEscalation()" style="margin-top:8px;padding:8px 16px;font-size:13px">
          Request Free Callback
        </button>
      </div>
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function handleChatKey(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

function autoResize(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

function clearChat() {
  state.sessionId = null;
  const container = document.getElementById('chat-messages');
  if (!container) return;
  container.innerHTML = `
    <div class="chat-message ai-message">
      <div class="msg-avatar">${ADVISOR_AVATAR}</div>
      <div class="msg-content">
        <div class="msg-bubble">
          <p>Session reset. How can I help you and your family today?</p>
        </div>
        <div class="msg-time">Just now</div>
      </div>
    </div>
  `;
  updateSentiment('neutral');
}

function sendQuickQuestion(text) {
  if (!text) return;
  const clean = text.replace(/[\u2192\u2190\u2191\u2193→←]/g, '').trim();
  const input = document.getElementById('chat-input');
  if (input) input.value = clean;
  sendMessage(clean);
}

async function translateLastMessage() {
  const bubbles = document.querySelectorAll('.ai-message .msg-bubble');
  if (bubbles.length === 0) {
    showToast('No messages to translate yet', 'info');
    return;
  }

  const last = bubbles[bubbles.length - 1];
  let text = last.getAttribute('data-original-text') || last.innerText.trim();
  if (!last.getAttribute('data-original-text')) {
    last.setAttribute('data-original-text', text);
  }

  const target = state.chatLang === 'en' ? 'hi' : 'en';
  last.style.opacity = '0.5';

  try {
    const res = await fetch(`${API}/translate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, target })
    });
    const data = await res.json();
    if (data.translated) {
      last.innerHTML = `
        <div class="translated-body">${formatMessageText(data.translated)}</div>
        <div style="margin-top:10px;padding-top:8px;border-top:1px solid #e2e8f0;font-size:12px;color:var(--text-muted);opacity:0.85">
          <strong>Original (${target === 'hi' ? 'English' : 'हिन्दी'}):</strong><br>
          ${formatMessageText(text)}
        </div>
      `;
      showToast(`Translated to ${target === 'hi' ? 'हिन्दी (Hindi)' : 'English'}`, 'success');
    } else {
      showToast('Translation returned empty text', 'error');
    }
    last.style.opacity = '1';
  } catch (e) {
    last.style.opacity = '1';
    showToast('Translation service unavailable', 'error');
  }
}

// Voice input
function startVoice() {
  const btn = document.getElementById('voice-btn');
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    showToast('Voice input not supported in this browser', 'error');
    return;
  }

  if (state.isRecording) {
    state.recognition?.stop();
    state.isRecording = false;
    btn.classList.remove('recording');
    return;
  }

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  state.recognition = new SR();
  state.recognition.lang = state.chatLang === 'hi' ? 'hi-IN' : 'en-IN';
  state.recognition.continuous = false;
  state.recognition.interimResults = false;

  state.recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    document.getElementById('chat-input').value = transcript;
    sendMessage();
  };

  state.recognition.onend = () => {
    state.isRecording = false;
    btn.classList.remove('recording');
  };

  state.recognition.start();
  state.isRecording = true;
  btn.classList.add('recording');
  showToast('Listening... Speak now', 'info');
}

// ══════════════════════════════════════════════════════════
// ESCALATION
// ══════════════════════════════════════════════════════════
function showEscalation() {
  const modal = document.getElementById('escalation-modal');
  if (modal) modal.style.display = 'flex';
}

function closeEscalation() {
  const modal = document.getElementById('escalation-modal');
  if (modal) modal.style.display = 'none';
}

function closeEscalationModal(event) {
  if (event.target === document.getElementById('escalation-modal')) {
    closeEscalation();
  }
}

async function submitEscalation() {
  const name = document.getElementById('esc-name')?.value;
  const phone = document.getElementById('esc-phone')?.value;
  const concern = document.getElementById('esc-concern')?.value;

  if (!phone) { showToast('Please enter your phone number', 'error'); return; }

  try {
    const res = await fetch(`${API}/escalate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: state.sessionId,
        name, phone, concern,
        trade_id: document.getElementById('trade-interest')?.value
      })
    });
    const data = await res.json();
    showToast(data.message, 'success');
    closeEscalation();

    appendMessage(
      `Your escalation request has been submitted (ID: ${data.request_id}). A human counsellor will call you at ${phone} within 24 hours. Reference ID: ${data.request_id}`,
      'ai'
    );
  } catch (e) {
    showToast('Escalation request submitted (offline mode)', 'success');
    closeEscalation();
  }
}

// ══════════════════════════════════════════════════════════
// ══════════════════════════════════════════════════════════
// ADMIN DASHBOARD & SECURITY SUITE
// ══════════════════════════════════════════════════════════
let adminTradesData = [];
let adminUsersData = [];

function checkAdminAccess() {
  const gateEl = document.getElementById('admin-gate-screen');
  const contentEl = document.getElementById('admin-content-screen');
  const errEl = document.getElementById('admin-gate-error');
  if (errEl) errEl.style.display = 'none';

  const user = state.currentUser;
  const isAdm = user && user.role === 'admin' && state.authToken;

  if (isAdm) {
    if (gateEl) gateEl.style.display = 'none';
    if (contentEl) contentEl.style.display = 'block';
    const nameEl = document.getElementById('admin-logged-name');
    if (nameEl) nameEl.textContent = user.full_name || user.username || 'System Administrator';
    loadAdminData();
  } else {
    if (gateEl) gateEl.style.display = 'flex';
    if (contentEl) contentEl.style.display = 'none';
  }
}

async function doAdminGateLogin() {
  const uInput = document.getElementById('admin-gate-username');
  const pInput = document.getElementById('admin-gate-password');
  const errEl = document.getElementById('admin-gate-error');
  const btn = document.getElementById('admin-gate-btn');

  const username = (uInput?.value || '').trim();
  const password = (pInput?.value || '').trim();

  if (!username || !password) {
    if (errEl) {
      errEl.textContent = 'Please enter both administrator username and password.';
      errEl.style.display = 'block';
    }
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span>Verifying credentials...</span>';
  }
  if (errEl) errEl.style.display = 'none';

  try {
    const res = await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();

    if (!res.ok) {
      if (errEl) {
        errEl.textContent = data.error || 'Authentication rejected.';
        errEl.style.display = 'block';
      }
      return;
    }

    if (data.role !== 'admin') {
      if (errEl) {
        errEl.textContent = 'Access Denied: This account does not possess administrator privileges. Only administrators can access this portal.';
        errEl.style.display = 'block';
      }
      return;
    }

    // Success - store admin session
    state.authToken = data.token;
    state.currentUser = data;
    localStorage.setItem('vg_token', data.token);
    localStorage.setItem('vg_user', JSON.stringify(data));
    updateAuthUI();

    showToast(`Administrator authenticated: ${data.full_name || data.username}`, 'success');
    checkAdminAccess();
  } catch (e) {
    if (errEl) {
      errEl.textContent = 'Server connection error during authentication.';
      errEl.style.display = 'block';
    }
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<span>Authenticate &amp; Access Dashboard</span>';
    }
  }
}

function doAdminLogout() {
  state.authToken = null;
  state.currentUser = null;
  localStorage.removeItem('vg_token');
  localStorage.removeItem('vg_user');
  updateAuthUI();
  showToast('Logged out of Administrator Portal', 'info');
  showSection('home');
}

async function adminFetch(url, options = {}) {
  options.headers = options.headers || {};
  if (state.authToken) {
    options.headers['X-Auth-Token'] = state.authToken;
  }
  if (!options.headers['Content-Type'] && options.method && options.method !== 'GET') {
    options.headers['Content-Type'] = 'application/json';
  }
  const res = await fetch(url, options);
  if (res.status === 401 || res.status === 403) {
    showToast('Admin session expired or access unauthorized. Please re-authenticate.', 'error');
    checkAdminAccess();
    throw new Error('Unauthorized');
  }
  return res;
}

function showAdminTab(name, btn) {
  document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.admin-nav-item').forEach(b => b.classList.remove('active'));
  document.getElementById(`tab-${name}`)?.classList.add('active');
  btn?.classList.add('active');

  if (name === 'overview') loadAdminData();
  if (name === 'trades-mgmt') loadTradesManagement();
  if (name === 'users-mgmt') loadUsersManagement();
  if (name === 'sessions') loadSessionsTable();
  if (name === 'resistance') loadResistanceMap();
  if (name === 'escalations') loadEscalations();
}

async function loadAdminData() {
  document.getElementById('admin-refresh-time').textContent = 'Refreshing...';

  try {
    // Check Ollama status
    const ollamaRes = await fetch(`${API}/ollama/status`);
    const ollamaData = await ollamaRes.json();
    const statusEl = document.getElementById('admin-ai-status');
    const dotEl = document.querySelector('.admin-tab-header .status-dot');
    if (ollamaData.status === 'online') {
      if (statusEl) statusEl.textContent = `AI: Online (${ollamaData.models.length} models)`;
      if (dotEl) dotEl.classList.add('online');
    } else {
      if (statusEl) statusEl.textContent = 'AI: Offline';
      if (dotEl) { dotEl.classList.remove('online'); dotEl.style.background = '#ef4444'; }
    }

    // Get stats with admin auth
    const statsRes = await adminFetch(`${API}/admin/stats`);
    const stats = await statsRes.json();
    state.adminData = stats;

    renderAdminKPIs(stats);
    renderTrendChart(stats.session_trend || []);
    renderSentimentChart(stats.sentiment_distribution || {});
    renderBarChart('concern-bars', stats.concern_distribution || {}, CONCERN_COLORS);
    renderBarChart('trade-bars', stats.trade_interest || {}, null, true);
    renderBarChart('lang-bars', stats.language_distribution || {}, {'en': '#6366f1', 'hi': '#f59e0b'});

    const now = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    document.getElementById('admin-refresh-time').textContent = `Last updated: ${now}`;
  } catch (e) {
    document.getElementById('admin-refresh-time').textContent = 'Server offline';
    renderMockAdminData();
  }
}

// ── TRADE MANAGEMENT (Admin CRUD) ──────────────────────────
async function loadTradesManagement() {
  const container = document.getElementById('admin-trades-container');
  if (!container) return;
  container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><span>Loading trade catalogue...</span></div>';

  try {
    const res = await adminFetch(`${API}/admin/trades`);
    adminTradesData = await res.json();
    populateAdminTradeSectors(adminTradesData);
    renderAdminTradesList(adminTradesData);
  } catch (e) {
    container.innerHTML = '<div class="empty-state"><p>Failed to load trades from server.</p></div>';
  }
}

function populateAdminTradeSectors(trades) {
  const sel = document.getElementById('admin-trade-sector-filter');
  if (!sel) return;
  const currentVal = sel.value;
  const sectors = [...new Set(trades.map(t => t.sector).filter(Boolean))].sort();
  sel.innerHTML = '<option value="all">All Sectors</option>' + 
    sectors.map(s => `<option value="${s}">${s}</option>`).join('');
  if (sectors.includes(currentVal)) sel.value = currentVal;
}

function filterAdminTrades() {
  const q = (document.getElementById('admin-trade-search')?.value || '').toLowerCase().trim();
  const sec = document.getElementById('admin-trade-sector-filter')?.value || 'all';

  const filtered = adminTradesData.filter(t => {
    const matchQ = !q || (t.name && t.name.toLowerCase().includes(q)) ||
                          (t.name_hi && t.name_hi.toLowerCase().includes(q)) ||
                          (t.sector && t.sector.toLowerCase().includes(q)) ||
                          (t.id && t.id.toLowerCase().includes(q));
    const matchSec = sec === 'all' || t.sector === sec;
    return matchQ && matchSec;
  });

  renderAdminTradesList(filtered);
}

function renderAdminTradesList(trades) {
  const container = document.getElementById('admin-trades-container');
  if (!container) return;

  if (trades.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1;text-align:center;padding:40px">
        <p>No trades match your search criteria.</p>
        <button class="btn-psu-primary" onclick="openTradeEditorModal()" style="margin-top:12px">Add New Trade</button>
      </div>`;
    return;
  }

  container.innerHTML = trades.map(t => {
    return `
      <div class="admin-trade-card" id="admin-card-${t.id}">
        <div class="atc-top">
          <div class="atc-title-box">
            <div>
              <div class="atc-name">${t.name}</div>
              <div class="atc-name-hi">${t.name_hi || ''}</div>
            </div>
          </div>
          <span class="atc-pill nsqf">NSQF ${t.nsqf_level || 4}</span>
        </div>
        <div class="atc-sector">${t.sector || 'Technical & Industrial'}</div>
        <div class="atc-pills">
          <span class="atc-pill">${t.duration_months || 12} Mos</span>
          <span class="atc-pill">${t.placement_rate || 85}% Placement</span>
          <span class="atc-pill">Self-emp: ${t.self_employment_potential || 'High'}</span>
        </div>
        <div class="atc-metrics">
          <div class="atc-metric">
            <div class="atc-metric-val">&#8377;${(t.avg_experienced_salary || 25000).toLocaleString('en-IN')}</div>
            <div class="atc-metric-lbl">Avg Monthly</div>
          </div>
          <div class="atc-metric">
            <div class="atc-metric-val">&#8377;${(t.top_salary || 50000).toLocaleString('en-IN')}</div>
            <div class="atc-metric-lbl">Top Earners</div>
          </div>
        </div>
        <div class="atc-actions">
          <button class="btn-action-edit" onclick="openTradeEditorModal('${t.id}')">Edit Trade</button>
          <button class="btn-action-delete" onclick="deleteTrade('${t.id}', '${(t.name || '').replace(/'/g, "\\'")}')">Delete</button>
        </div>
      </div>
    `;
  }).join('');
}

function openTradeEditorModal(tid = null) {
  const modal = document.getElementById('modal-trade-editor');
  const titleEl = document.getElementById('trade-modal-title');
  const idInput = document.getElementById('tf-id');
  const isEditInput = document.getElementById('tf-is-edit');
  if (!modal) return;

  if (tid) {
    const trade = adminTradesData.find(t => t.id === tid) || (state.trades ? state.trades.find(t => t.id === tid) : null);
    if (!trade) return;
    if (titleEl) titleEl.innerHTML = `Edit NSQF Trade: <strong>${trade.name}</strong>`;
    if (isEditInput) isEditInput.value = '1';
    if (idInput) {
      idInput.value = trade.id;
      idInput.disabled = true;
    }
    document.getElementById('tf-icon').value = 'Technical';
    document.getElementById('tf-name').value = trade.name || '';
    document.getElementById('tf-name-hi').value = trade.name_hi || '';
    document.getElementById('tf-sector').value = trade.sector || '';
    document.getElementById('tf-sector-hi').value = trade.sector_hi || '';
    document.getElementById('tf-nsqf').value = trade.nsqf_level || 4;
    document.getElementById('tf-duration').value = trade.duration_months || 12;
    document.getElementById('tf-placement').value = trade.placement_rate || 85;
    document.getElementById('tf-salary-start').value = trade.avg_starting_salary || 12000;
    document.getElementById('tf-salary-exp').value = trade.avg_experienced_salary || 26000;
    document.getElementById('tf-salary-top').value = trade.top_salary || 55000;
    document.getElementById('tf-self-emp').value = trade.self_employment_potential || 'High';
    document.getElementById('tf-safety').value = trade.safety_rating || 'Low';
    document.getElementById('tf-desc').value = trade.description || '';
    document.getElementById('tf-employers').value = Array.isArray(trade.top_employers) ? trade.top_employers.join(', ') : (trade.top_employers || '');
  } else {
    if (titleEl) titleEl.innerHTML = 'Add New NSQF Trade';
    if (isEditInput) isEditInput.value = '0';
    if (idInput) {
      idInput.value = '';
      idInput.disabled = false;
    }
    document.getElementById('tf-icon').value = 'Technical';
    document.getElementById('tf-name').value = '';
    document.getElementById('tf-name-hi').value = '';
    document.getElementById('tf-sector').value = 'Engineering & Technology';
    document.getElementById('tf-sector-hi').value = 'इंजीनियरिंग और प्रौद्योगिकी';
    document.getElementById('tf-nsqf').value = 4;
    document.getElementById('tf-duration').value = 12;
    document.getElementById('tf-placement').value = 88;
    document.getElementById('tf-salary-start').value = 14000;
    document.getElementById('tf-salary-exp').value = 28000;
    document.getElementById('tf-salary-top').value = 60000;
    document.getElementById('tf-self-emp').value = 'High';
    document.getElementById('tf-safety').value = 'Low';
    document.getElementById('tf-desc').value = '';
    document.getElementById('tf-employers').value = 'Tata Projects, L&T, State PSUs';
  }

  modal.style.display = 'flex';
}

function closeTradeModalEditor() {
  const modal = document.getElementById('modal-trade-editor');
  if (modal) modal.style.display = 'none';
}

async function saveTrade() {
  const isEdit = document.getElementById('tf-is-edit')?.value === '1';
  const tid = (document.getElementById('tf-id')?.value || '').trim().toLowerCase().replace(/[^a-z0-9_]/g, '_');
  const name = (document.getElementById('tf-name')?.value || '').trim();
  const name_hi = (document.getElementById('tf-name-hi')?.value || '').trim();
  const sector = (document.getElementById('tf-sector')?.value || '').trim();
  const sector_hi = (document.getElementById('tf-sector-hi')?.value || '').trim();
  const nsqf_level = parseInt(document.getElementById('tf-nsqf')?.value) || 4;
  const duration_months = parseInt(document.getElementById('tf-duration')?.value) || 12;
  const placement_rate = parseInt(document.getElementById('tf-placement')?.value) || 85;
  const avg_starting_salary = parseInt(document.getElementById('tf-salary-start')?.value) || 12000;
  const avg_experienced_salary = parseInt(document.getElementById('tf-salary-exp')?.value) || 26000;
  const top_salary = parseInt(document.getElementById('tf-salary-top')?.value) || 55000;
  const self_employment_potential = document.getElementById('tf-self-emp')?.value || 'High';
  const safety_rating = document.getElementById('tf-safety')?.value || 'Low';
  const description = document.getElementById('tf-desc')?.value || '';
  const icon = (document.getElementById('tf-icon')?.value || '').trim();
  const employersStr = document.getElementById('tf-employers')?.value || '';
  const top_employers = employersStr.split(',').map(s => s.trim()).filter(Boolean);

  if (!tid || !name) {
    showToast('Trade ID and Name are required', 'error');
    return;
  }

  if (icon) {
    TRADE_ICONS[tid] = icon;
  }

  const payload = {
    id: tid,
    name,
    name_hi: name_hi || name,
    sector: sector || 'Technical & Industrial',
    sector_hi: sector_hi || 'तकनीकी और औद्योगिक',
    nsqf_level,
    duration_months,
    placement_rate,
    avg_starting_salary,
    avg_experienced_salary,
    top_salary,
    self_employment_potential,
    safety_rating,
    description,
    description_hi: description,
    top_employers
  };

  const btn = document.getElementById('btn-save-trade');
  if (btn) { btn.disabled = true; btn.textContent = 'Saving...'; }

  try {
    const url = isEdit ? `${API}/admin/trades/${tid}` : `${API}/admin/trades`;
    const method = isEdit ? 'PUT' : 'POST';
    const res = await adminFetch(url, { method, body: JSON.stringify(payload) });
    const data = await res.json();

    if (!res.ok) {
      showToast(data.error || 'Failed to save trade', 'error');
      return;
    }

    closeTradeModalEditor();
    showToast(`Trade "${name}" saved successfully`, 'success');
    loadTradesManagement();
    loadTrades(); // sync public trade explorer
    populateTradeSelector(); // sync counsellor trade dropdown
  } catch (e) {
    showToast('Failed to save trade: ' + e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Save Trade'; }
  }
}

async function deleteTrade(tid, tradeName) {
  if (!confirm(`Are you sure you want to delete trade "${tradeName || tid}"?\n\nThis will remove it from the trade catalogue, live counsellor, and public explore screens.`)) {
    return;
  }

  try {
    const res = await adminFetch(`${API}/admin/trades/${tid}`, { method: 'DELETE' });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.error || 'Failed to delete trade', 'error');
      return;
    }
    showToast(`Trade deleted successfully`, 'success');
    loadTradesManagement();
    loadTrades();
    populateTradeSelector();
  } catch (e) {
    showToast('Failed to delete trade: ' + e.message, 'error');
  }
}

// ── USER MANAGEMENT (Admin User Directory) ───────────────────
async function loadUsersManagement() {
  const tbody = document.getElementById('admin-users-tbody');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="6" class="table-loading">Loading users...</td></tr>';

  try {
    const res = await adminFetch(`${API}/admin/users`);
    adminUsersData = await res.json();
    renderAdminUsersTable(adminUsersData);
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="6" class="table-loading">Failed to load users</td></tr>';
  }
}

function renderAdminUsersTable(users) {
  const tbody = document.getElementById('admin-users-tbody');
  if (!tbody) return;

  if (users.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:24px">No users found.</td></tr>';
    return;
  }

  const currentUid = state.currentUser ? state.currentUser.id : null;

  tbody.innerHTML = users.map(u => {
    const isSelf = currentUid && (u.id === currentUid || u.username === state.currentUser?.username);
    const regDate = u.created_at ? new Date(u.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Recent';
    const roleBadge = u.role === 'admin' 
      ? '<span class="badge-role admin">Administrator</span>' 
      : '<span class="badge-role user">Learner / Parent</span>';
    const statusBadge = u.is_active !== 0
      ? '<span class="badge-status active">Active</span>'
      : '<span class="badge-status inactive">Disabled</span>';
    const roleBtnText = u.role === 'admin' ? 'Demote to User' : 'Promote to Admin';

    return `
      <tr>
        <td>
          <div style="font-weight:700;color:var(--psu-navy)">${u.full_name || u.username}</div>
          <div style="font-size:11px;color:var(--text-muted)">@${u.username}</div>
        </td>
        <td>${roleBadge}</td>
        <td>
          <div style="font-size:12px">${u.phone || u.email || 'N/A'}</div>
        </td>
        <td>${statusBadge}</td>
        <td style="font-size:12px;color:var(--text-muted)">${regDate}</td>
        <td>
          <div class="table-btn-group">
            <button class="table-btn table-btn-toggle" onclick="toggleUserStatus('${u.id}')" title="Toggle active status">
              ${u.is_active !== 0 ? 'Disable' : 'Enable'}
            </button>
            <button class="table-btn table-btn-role" onclick="changeUserRole('${u.id}', '${u.role}', '${(u.username || '').replace(/'/g, "\\'")}')">
              ${roleBtnText}
            </button>
            ${!isSelf ? `
              <button class="table-btn table-btn-del" onclick="deleteUser('${u.id}', '${(u.username || '').replace(/'/g, "\\'")}')" title="Delete account">
                Delete
              </button>
            ` : '<span style="font-size:11px;color:var(--text-muted);font-weight:600">(You)</span>'}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function openUserCreatorModal() {
  const modal = document.getElementById('modal-user-creator');
  if (!modal) return;
  document.getElementById('uf-fullname').value = '';
  document.getElementById('uf-username').value = '';
  document.getElementById('uf-password').value = '';
  document.getElementById('uf-phone').value = '';
  document.getElementById('uf-role').value = 'user';
  modal.style.display = 'flex';
}

function closeUserCreatorModal() {
  const modal = document.getElementById('modal-user-creator');
  if (modal) modal.style.display = 'none';
}

async function saveNewUser() {
  const full_name = (document.getElementById('uf-fullname')?.value || '').trim();
  const username = (document.getElementById('uf-username')?.value || '').trim();
  const password = (document.getElementById('uf-password')?.value || '').trim();
  const phone = (document.getElementById('uf-phone')?.value || '').trim();
  const role = document.getElementById('uf-role')?.value || 'user';

  if (!username || !password) {
    showToast('Username and password are required', 'error');
    return;
  }

  const btn = document.getElementById('btn-save-user');
  if (btn) { btn.disabled = true; btn.textContent = 'Creating...'; }

  try {
    const res = await adminFetch(`${API}/admin/users`, {
      method: 'POST',
      body: JSON.stringify({ username, password, full_name, phone, role })
    });
    const data = await res.json();

    if (!res.ok) {
      showToast(data.error || 'Failed to create user', 'error');
      return;
    }

    closeUserCreatorModal();
    showToast(`Account created for "${username}" with role ${role.toUpperCase()}`, 'success');
    loadUsersManagement();
  } catch (e) {
    showToast('Failed to create user: ' + e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Create User'; }
  }
}

async function toggleUserStatus(uid) {
  try {
    const res = await adminFetch(`${API}/admin/users/${uid}/toggle`, { method: 'POST' });
    if (!res.ok) {
      showToast('Failed to toggle user status', 'error');
      return;
    }
    showToast('User status updated', 'success');
    loadUsersManagement();
  } catch (e) {
    showToast('Error toggling user: ' + e.message, 'error');
  }
}

async function changeUserRole(uid, currentRole, username) {
  const nextRole = currentRole === 'admin' ? 'user' : 'admin';
  if (!confirm(`Change role of user "${username}" from ${currentRole.toUpperCase()} to ${nextRole.toUpperCase()}?`)) {
    return;
  }

  try {
    const res = await adminFetch(`${API}/admin/users/${uid}/role`, {
      method: 'POST',
      body: JSON.stringify({ role: nextRole })
    });
    if (!res.ok) {
      showToast('Failed to update role', 'error');
      return;
    }
    showToast(`User "${username}" updated to ${nextRole.toUpperCase()}`, 'success');
    loadUsersManagement();
  } catch (e) {
    showToast('Error updating role: ' + e.message, 'error');
  }
}

async function deleteUser(uid, username) {
  if (!confirm(`Permanently delete account for user "${username}"?\n\nThis action cannot be undone.`)) {
    return;
  }

  try {
    const res = await adminFetch(`${API}/admin/users/${uid}`, { method: 'DELETE' });
    if (!res.ok) {
      showToast('Failed to delete user', 'error');
      return;
    }
    showToast(`User account deleted`, 'success');
    loadUsersManagement();
  } catch (e) {
    showToast('Error deleting user: ' + e.message, 'error');
  }
}

function renderMockAdminData() {
  // Render with sample data for demo
  const mockStats = {
    total_sessions: 142, total_messages: 876,
    avg_messages_per_session: 6.2,
    escalation_stats: { total: 18, pending: 7, resolved: 11 },
    sentiment_distribution: { positive: 58, neutral: 62, concerned: 22 },
    concern_distribution: { income: 45, safety: 28, social_status: 22, career_growth: 31 },
    trade_interest: { electrician: 38, computer_operator: 29, healthcare_assistant: 24, beauty_wellness: 18 },
    language_distribution: { en: 89, hi: 53 },
    session_trend: [
      { date: 'Sep 25', sessions: 12 }, { date: 'Sep 26', sessions: 18 },
      { date: 'Sep 27', sessions: 9 }, { date: 'Sep 28', sessions: 21 },
      { date: 'Sep 29', sessions: 16 }, { date: 'Sep 30', sessions: 24 },
      { date: 'Oct 1', sessions: 19 }
    ]
  };
  renderAdminKPIs(mockStats);
  renderTrendChart(mockStats.session_trend);
  renderSentimentChart(mockStats.sentiment_distribution);
  renderBarChart('concern-bars', mockStats.concern_distribution, CONCERN_COLORS);
  renderBarChart('trade-bars', mockStats.trade_interest, null, true);
  renderBarChart('lang-bars', mockStats.language_distribution, {'en': '#6366f1', 'hi': '#f59e0b'});
}

function renderAdminKPIs(stats) {
  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  set('kpi-sessions', stats.total_sessions || 0);
  set('kpi-messages', stats.total_messages || 0);
  set('kpi-avg', stats.avg_messages_per_session || 0);
  set('kpi-escalations', stats.escalation_stats?.total || 0);
  set('kpi-esc-pending', `${stats.escalation_stats?.pending || 0} pending`);

  const sentDist = stats.sentiment_distribution || {};
  const total = Object.values(sentDist).reduce((a, b) => a + b, 0);
  const concernedPct = total > 0 ? Math.round((sentDist.concerned || 0) / total * 100) : 0;
  set('kpi-concerned', `${concernedPct}%`);
}

function renderTrendChart(trend) {
  const container = document.getElementById('trend-chart');
  if (!container || trend.length === 0) return;

  const W = container.offsetWidth || 500;
  const H = 160;
  const pad = { top: 20, right: 20, bottom: 40, left: 40 };
  const iW = W - pad.left - pad.right;
  const iH = H - pad.top - pad.bottom;

  const maxV = Math.max(...trend.map(d => d.sessions), 1);
  const pts = trend.map((d, i) => {
    const x = pad.left + (i / (trend.length - 1)) * iW;
    const y = pad.top + (1 - d.sessions / maxV) * iH;
    return { x, y, ...d };
  });

  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ');
  const area = `${line} L${pts[pts.length-1].x},${H-pad.bottom} L${pts[0].x},${H-pad.bottom} Z`;

  container.innerHTML = `
    <svg width="100%" height="${H}" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#6366f1" stop-opacity="0.3"/>
          <stop offset="100%" stop-color="#6366f1" stop-opacity="0"/>
        </linearGradient>
      </defs>
      <path d="${area}" fill="url(#areaGrad)"/>
      <path d="${line}" fill="none" stroke="#6366f1" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
      ${pts.map(p => `
        <circle cx="${p.x}" cy="${p.y}" r="4" fill="#6366f1" stroke="#0a0a0f" stroke-width="2"/>
        <text x="${p.x}" y="${H - 8}" text-anchor="middle" fill="#64748b" font-size="10">${p.date.split(' ')[1] || p.date}</text>
        <text x="${p.x}" y="${p.y - 10}" text-anchor="middle" fill="#94a3b8" font-size="10">${p.sessions}</text>
      `).join('')}
    </svg>
  `;
}

function renderSentimentChart(dist) {
  const canvas = document.getElementById('sentiment-chart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const data = [
    { label: 'Positive', value: dist.positive || 0, color: '#10b981' },
    { label: 'Neutral', value: dist.neutral || 0, color: '#64748b' },
    { label: 'Concerned', value: dist.concerned || 0, color: '#f59e0b' }
  ];

  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  const cx = 100, cy = 100, r = 70, inner = 45;

  ctx.clearRect(0, 0, 200, 200);

  let angle = -Math.PI / 2;
  data.forEach(d => {
    const slice = (d.value / total) * 2 * Math.PI;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, angle, angle + slice);
    ctx.closePath();
    ctx.fillStyle = d.color;
    ctx.fill();
    angle += slice;
  });

  // Donut hole
  ctx.beginPath();
  ctx.arc(cx, cy, inner, 0, 2 * Math.PI);
  ctx.fillStyle = '#13131f';
  ctx.fill();

  // Center text
  ctx.fillStyle = '#f8fafc';
  ctx.font = 'bold 20px Inter';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(total, cx, cy - 8);
  ctx.font = '10px Inter';
  ctx.fillStyle = '#64748b';
  ctx.fillText('Total', cx, cy + 12);

  // Legend
  const legend = document.getElementById('sentiment-legend');
  if (legend) {
    legend.innerHTML = data.map(d => `
      <div class="legend-item">
        <div class="legend-dot" style="background:${d.color}"></div>
        <span>${d.label}: <strong>${d.value}</strong></span>
      </div>
    `).join('');
  }
}

function renderBarChart(containerId, data, colors, useTrade) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const max = Math.max(...entries.map(e => e[1]), 1);

  const BAR_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

  container.innerHTML = entries.map(([key, val], i) => {
    const pct = (val / max * 100).toFixed(0);
    const color = colors?.[key] || BAR_COLORS[i % BAR_COLORS.length];
    const label = useTrade
      ? (state.trades.find(t => t.id === key)?.name || key)
      : key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

    return `
      <div class="bar-item">
        <div class="bar-label" title="${label}">${label}</div>
        <div class="bar-track">
          <div class="bar-fill" style="width:0%;background:${color}" data-w="${pct}%"></div>
        </div>
        <div class="bar-value">${val}</div>
      </div>
    `;
  }).join('');

  requestAnimationFrame(() => {
    container.querySelectorAll('.bar-fill[data-w]').forEach(bar => {
      setTimeout(() => { bar.style.width = bar.dataset.w; }, 100);
    });
  });
}

async function loadSessionsTable() {
  const tbody = document.getElementById('sessions-tbody');
  if (!tbody) return;

  try {
    const res = await adminFetch(`${API}/admin/sessions`);
    const sessions = await res.json();

    if (sessions.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="table-loading">No sessions yet.</td></tr>';
      return;
    }

    tbody.innerHTML = sessions.map(s => `
      <tr>
        <td><code style="font-size:12px;color:var(--primary-light)">${s.session_id}</code></td>
        <td>${s.trade_id ? (state.trades.find(t => t.id === s.trade_id)?.name || s.trade_id) : 'None'}</td>
        <td>${s.location || 'Not specified'}</td>
        <td>${s.message_count}</td>
        <td><span style="padding:3px 10px;border-radius:20px;font-size:11px;background:rgba(99,102,241,0.1);color:#818cf8">${s.language?.toUpperCase() || 'EN'}</span></td>
        <td><span class="sentiment-pill ${s.last_sentiment}">${s.last_sentiment}</span></td>
        <td>${(s.concern_topics || []).map(c => `<span class="rl-item ${c}" style="font-size:10px;padding:2px 8px;">${c}</span>`).join(' ') || 'None'}</td>
        <td style="font-size:11px;color:var(--text-muted)">${s.created_at ? new Date(s.created_at).toLocaleString('en-IN') : 'N/A'}</td>
      </tr>
    `).join('');
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="8" class="table-loading">Loading sessions... (server starting)</td></tr>';
  }
}

async function loadResistanceMap() {
  const grid = document.getElementById('resistance-grid');
  if (!grid) return;

  try {
    const res = await adminFetch(`${API}/admin/resistance-map`);
    const data = await res.json();

    if (Object.keys(data).length === 0) {
      // Show sample data
      renderResistanceGrid({
        'Uttar Pradesh': { income: 42, social_status: 31, safety: 18, career_growth: 24 },
        'Bihar': { income: 38, safety: 15, social_status: 28, career_growth: 19 },
        'Rajasthan': { income: 29, social_status: 22, female_safety: 35, career_growth: 18 },
        'Maharashtra': { income: 18, career_growth: 25, safety: 12 },
        'West Bengal': { income: 22, social_status: 19, career_growth: 28 }
      });
    } else {
      renderResistanceGrid(data);
    }
  } catch (e) {
    renderResistanceGrid({
      'North India': { income: 45, social_status: 35, safety: 20 },
      'East India': { income: 38, social_status: 28, career_growth: 22 },
      'Central India': { income: 41, female_safety: 30, social_status: 25 }
    });
  }
}

function renderResistanceGrid(data) {
  const grid = document.getElementById('resistance-grid');
  if (!grid) return;

  const concernColors = {
    income: '#f59e0b', safety: '#ef4444', social_status: '#6366f1',
    career_growth: '#10b981', female_safety: '#ec4899', general: '#64748b'
  };

  grid.innerHTML = Object.entries(data).map(([location, concerns]) => {
    const sortedConcerns = Object.entries(concerns).sort((a, b) => b[1] - a[1]);
    const maxVal = Math.max(...Object.values(concerns), 1);

    return `
      <div class="resistance-card">
        <div class="rc-location">${location}</div>
        <div class="rc-concerns">
          ${sortedConcerns.map(([concern, count]) => `
            <div class="rc-concern">
              <span style="font-size:12px;color:${concernColors[concern]};width:80px;flex-shrink:0">${concern.replace(/_/g, ' ')}</span>
              <div class="rc-concern-bar-track">
                <div class="rc-concern-bar-fill" style="width:${(count/maxVal*100).toFixed(0)}%;background:${concernColors[concern]}"></div>
              </div>
              <span style="font-size:11px;color:var(--text-muted);width:24px;text-align:right">${count}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }).join('');
}

async function loadEscalations() {
  const list = document.getElementById('escalations-list');
  if (!list) return;

  try {
    const res = await adminFetch(`${API}/admin/escalations`);
    const escs = await res.json();

    if (escs.length === 0) {
      list.innerHTML = `<div class="empty-state"><p>No escalation requests yet.</p></div>`;
      return;
    }

    list.innerHTML = escs.map(e => `
      <div class="escalation-card" id="esc-${e.request_id}">
        <div class="esc-card-info">
          <div class="esc-card-name">${e.name || 'Anonymous'}</div>
          <div class="esc-card-meta">
            <span>Phone: ${e.phone || 'N/A'}</span>
            <span>Location: ${e.location || 'Unknown'}</span>
            <span>Trade: ${e.trade_id || 'General'}</span>
            <span>Sentiment: ${e.sentiment || 'neutral'}</span>
            <span>${e.message_count || 0} messages</span>
          </div>
          ${e.concern ? `<div style="margin-top:8px;font-size:13px;color:var(--text-secondary);padding:8px;background:var(--bg-card);border-radius:8px">${e.concern}</div>` : ''}
          <div style="font-size:11px;color:var(--text-muted);margin-top:8px">
            Submitted: ${new Date(e.created_at).toLocaleString('en-IN')}
          </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px;flex-shrink:0">
          <span class="esc-card-status ${e.status}">${e.status}</span>
          ${e.status === 'pending' ? `<button class="resolve-btn" onclick="resolveEscalation('${e.request_id}')">Mark Resolved</button>` : ''}
        </div>
      </div>
    `).join('');
  } catch (e) {
    list.innerHTML = `<div class="empty-state"><p>No escalation requests yet.</p></div>`;
  }
}

async function resolveEscalation(reqId) {
  try {
    await adminFetch(`${API}/admin/escalations/${reqId}/resolve`, { method: 'POST' });
    showToast('Escalation marked as resolved', 'success');
    loadEscalations();
  } catch (e) {
    showToast('Error resolving escalation', 'error');
  }
}

// ══════════════════════════════════════════════════════════
// UTILITIES
// ══════════════════════════════════════════════════════════
function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.className = `toast show ${type}`;
  setTimeout(() => toast.classList.remove('show'), 3000);
}

// ════════════════════════════════════════════════════════
// AUTH
// ════════════════════════════════════════════════════════
function showAuthModal(mode='login') {
  const modal=document.getElementById('auth-modal');
  if(modal) modal.style.display='flex';
  document.querySelectorAll('.auth-tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.auth-panel').forEach(p=>p.classList.remove('active'));
  document.getElementById(`tab-${mode}`)?.classList.add('active');
  document.getElementById(`panel-${mode}`)?.classList.add('active');
}
function closeAuthModal(e) {
  if(!e||e.target===document.getElementById('auth-modal'))
    document.getElementById('auth-modal').style.display='none';
}
async function doLogin() {
  const username=document.getElementById('login-username').value.trim();
  const password=document.getElementById('login-password').value.trim();
  if(!username||!password){showToast('Enter username and password','error');return;}
  const res=await fetch(`${API}/auth/login`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})}).catch(()=>null);
  if(!res){showToast('Connection error','error');return;}
  const data=await res.json();
  if(!res.ok){showToast(data.error||'Login failed','error');return;}
  state.authToken=data.token; state.currentUser=data;
  localStorage.setItem('vg_token',data.token);
  localStorage.setItem('vg_user',JSON.stringify(data));
  document.getElementById('auth-modal').style.display='none';
  updateAuthUI();
  checkAdminAccess();
  showToast(`Welcome, ${data.full_name||data.username}!`,'success');
}
async function doRegister() {
  const username=document.getElementById('reg-username').value.trim();
  const password=document.getElementById('reg-password').value.trim();
  const full_name=document.getElementById('reg-fullname').value.trim();
  const phone=document.getElementById('reg-phone').value.trim();
  if(!username||!password){showToast('Fill required fields','error');return;}
  const res=await fetch(`${API}/auth/register`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password,full_name,phone})}).catch(()=>null);
  if(!res){showToast('Connection error','error');return;}
  const data=await res.json();
  if(!res.ok){showToast(data.error||'Registration failed','error');return;}
  state.authToken=data.token; state.currentUser=data;
  localStorage.setItem('vg_token',data.token);
  localStorage.setItem('vg_user',JSON.stringify(data));
  document.getElementById('auth-modal').style.display='none';
  updateAuthUI(); showToast(`Account created! Welcome, ${username}`,'success');
}
function doLogout() {
  state.authToken=null; state.currentUser=null;
  localStorage.removeItem('vg_token'); localStorage.removeItem('vg_user');
  updateAuthUI();
  checkAdminAccess();
  showToast('Logged out','success');
}
function updateAuthUI() {
  const user=state.currentUser;
  const loginBtn=document.getElementById('auth-login-btn');
  const userChip=document.getElementById('user-chip');
  if(user) {
    if(loginBtn) loginBtn.style.display='none';
    if(userChip) { userChip.style.display='flex'; userChip.innerHTML=`<span>${user.full_name||user.username}</span><button onclick="doLogout()" style="background:none;border:none;color:var(--psu-orange);cursor:pointer;font-size:12px;font-weight:600;padding:0 6px;margin-left:6px" title="Sign Out">Sign Out</button>`; }
  } else {
    if(loginBtn) loginBtn.style.display='block';
    if(userChip) userChip.style.display='none';
  }
}

// ════════════════════════════════════════════════════════
// WHATSAPP-STYLE VOICE MESSAGES
// ════════════════════════════════════════════════════════
async function toggleVoiceMessage() {
  const btn=document.getElementById('vm-btn');
  const bar=document.getElementById('voice-recording-bar');
  if (state.isVoiceRecording) {
    state.mediaRecorder?.stop();
    state.isVoiceRecording=false;
    btn?.classList.remove('recording-pulse');
    if(bar) bar.style.display='none';
    return;
  }
  try {
    const stream=await navigator.mediaDevices.getUserMedia({audio:true});
    state.voiceChunks=[];
    const mimeType=MediaRecorder.isTypeSupported('audio/webm')?'audio/webm':'audio/ogg';
    state.mediaRecorder=new MediaRecorder(stream,{mimeType});
    state.mediaRecorder.ondataavailable=e=>state.voiceChunks.push(e.data);
    state.mediaRecorder.onstop=async()=>{
      stream.getTracks().forEach(t=>t.stop());
      await sendVoiceMessage(new Blob(state.voiceChunks,{type:mimeType}));
    };
    state.mediaRecorder.start();
    state.isVoiceRecording=true;
    btn?.classList.add('recording-pulse');
    if(bar) bar.style.display='flex';
    showToast('Recording... tap again to send', 'info');
    setTimeout(()=>{if(state.isVoiceRecording)toggleVoiceMessage();},60000);
  } catch(e) { showToast('Microphone access denied','error'); }
}

async function sendVoiceMessage(blob) {
  setTyping(true);
  appendVoiceBubble(blob,'user');
  const formData=new FormData();
  formData.append('audio',blob,'voice.webm');
  formData.append('lang',state.chatLang);
  if(state.sessionId) formData.append('session_id',state.sessionId);
  const tradeId=document.getElementById('trade-interest')?.value;
  if(tradeId) formData.append('trade_id',tradeId);
  try {
    const res=await fetch(`${API}/voice/chat`,{method:'POST',body:formData});
    const data=await res.json();
    setTyping(false);
    if(data.error){appendMessage(data.error,'ai');return;}
    if(!state.sessionId&&data.session_id) state.sessionId=data.session_id;
    if(data.transcript){ const inp=document.getElementById('chat-input'); if(inp) inp.value=data.transcript; }
    appendAIVoiceMessage(data.response_text,data.audio);
    updateSentiment(data.sentiment);
  } catch(e){setTyping(false);appendMessage('Voice processing failed. Type instead.','ai');}
}

const PLAY_ICON = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
const PAUSE_ICON = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>`;

function appendVoiceBubble(blob,role){
  const container=document.getElementById('chat-messages');
  const url=URL.createObjectURL(blob);
  const now=new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'});
  const div=document.createElement('div');
  div.className=`chat-message ${role}-message`;
  const bars=Array(20).fill('').map(()=>`<span style="height:${8+Math.random()*16}px"></span>`).join('');
  div.innerHTML=`<div class="msg-avatar">${role==='user'?USER_AVATAR:ADVISOR_AVATAR}</div><div class="msg-content"><div class="msg-bubble voice-bubble"><div class="voice-msg"><button class="voice-play-btn" onclick="playVoiceSrc(this,'${url}')">${PLAY_ICON}</button><div class="voice-waveform">${bars}</div><span class="voice-duration">Voice</span></div></div><div class="msg-time">${now} Voice</div></div>`;
  container.appendChild(div);
  container.scrollTop=container.scrollHeight;
}

function appendAIVoiceMessage(text,audioResult){
  const container=document.getElementById('chat-messages');
  const now=new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'});
  const div=document.createElement('div');
  div.className='chat-message ai-message';
  let audioHtml='';
  if(audioResult&&audioResult.audioContent){
    const bars=Array(20).fill('').map(()=>`<span style="height:${6+Math.random()*14}px"></span>`).join('');
    audioHtml=`<div class="voice-msg ai-voice" style="margin-top:8px"><button class="voice-play-btn" onclick="playAudioB64('${audioResult.audioContent}',this)">${PLAY_ICON}</button><div class="voice-waveform ai-wave">${bars}</div><span class="voice-duration">TTS</span></div>`;
  }
  div.innerHTML=`<div class="msg-avatar">${ADVISOR_AVATAR}</div><div class="msg-content"><div class="msg-bubble">${formatMessageText(text)}${audioHtml}</div><div class="msg-time">${now}</div></div>`;
  container.appendChild(div);
  container.scrollTop=container.scrollHeight;
}

function playVoiceSrc(btn,url){
  const a=new Audio(url); btn.innerHTML=PAUSE_ICON;
  a.play(); a.onended=()=>{btn.innerHTML=PLAY_ICON;};
}
function playAudioB64(b64,btn){
  const a=new Audio(`data:audio/wav;base64,${b64}`);
  if(btn) btn.innerHTML=PAUSE_ICON;
  a.play(); a.onended=()=>{if(btn)btn.innerHTML=PLAY_ICON;};
}
async function speakText(text){
  try{
    const res=await fetch(`${API}/voice/synthesize`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,lang:state.chatLang,gender:'female'})});
    const data=await res.json();
    if(data.audioContent) playAudioB64(data.audioContent,null);
  }catch(e){}
}

// Accessibility: Font Resizer (A- / A / A+)
function setFontSize(size) {
  const root = document.documentElement;
  if (size === 'sm') root.style.fontSize = '14px';
  else if (size === 'lg') root.style.fontSize = '18px';
  else root.style.fontSize = '16px';
  document.querySelectorAll('.font-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`font-${size}`)?.classList.add('active');
}

// Responsive Mobile Menu
function toggleMobileMenu() {
  const nav = document.getElementById('nav-links');
  if (nav) nav.classList.toggle('open');
}

// Navbar scroll shadow effect
window.addEventListener('scroll', () => {
  const navbar = document.getElementById('navbar');
  if (navbar) {
    if (window.scrollY > 20) {
      navbar.style.boxShadow = '0 6px 20px rgba(0, 43, 73, 0.25)';
    } else {
      navbar.style.boxShadow = '0 4px 14px rgba(0, 43, 73, 0.15)';
    }
  }
});

// ══════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  // Restore logged in user session if available
  const savedToken = localStorage.getItem('vg_token');
  const savedUser = localStorage.getItem('vg_user');
  if (savedToken && savedUser) {
    try {
      state.authToken = savedToken;
      state.currentUser = JSON.parse(savedUser);
      updateAuthUI();
    } catch(e) {}
  }

  populateQuickQuestions();
  applyTranslations();

  // Admin data loads securely upon authenticated administrator access

  // Delegate clicks on interactive chat message list items
  document.getElementById('chat-messages')?.addEventListener('click', (e) => {
    const li = e.target.closest('.ai-message .msg-bubble li');
    if (li && !e.target.closest('button, a')) {
      sendQuickQuestion(li.textContent);
    }
  });

  // Check if trades modal should be shown from URL hash
  if (window.location.hash) {
    const section = window.location.hash.replace('#', '');
    if (['home', 'trades', 'counsellor', 'admin'].includes(section)) {
      showSection(section);
    }
  }

  console.log('VocGuide initialized successfully');
  console.log('Connecting to backend at http://localhost:5000');
});
