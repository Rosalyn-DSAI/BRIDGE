/* ==========================================================================
   BRIDGE · interface layer
   Plain JavaScript. No build step, no external dependencies, no inline
   styles — everything works under the app's strict Content-Security-Policy.
   All API calls, request shapes and response handling are unchanged from the
   original backend contracts.
   ========================================================================== */
'use strict';

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

/* --------------------------------------------------------------------------
   Constants
   -------------------------------------------------------------------------- */
const LANGUAGES = { en: 'English', zh: '简体中文', ja: '日本語', es: 'Español' };

const WORDS = {
  en: {
    meaning: 'What this means', actions: 'Instructions in the message',
    source: 'Show source', task: 'Track this task', missing: 'Conditions & missing details',
    vocab: 'Useful words', none: 'No explicit action was found.',
    when: 'When', where: 'Where', conditions: 'Conditions', steps: 'Steps',
  },
  zh: {
    meaning: '这是什么意思', actions: '原文中的要求', source: '查看原文',
    task: '跟踪此任务', missing: '条件和缺失信息', vocab: '实用词语',
    none: '未发现明确的行动要求。', when: '时间', where: '地点', conditions: '条件', steps: '步骤',
  },
  ja: {
    meaning: 'わかりやすい説明', actions: '原文の指示', source: '原文を確認',
    task: 'このタスクを管理', missing: '条件と不足している情報', vocab: '役立つ言葉',
    none: '明確な指示は見つかりませんでした。', when: '日時', where: '場所', conditions: '条件', steps: '手順',
  },
  es: {
    meaning: 'Qué significa', actions: 'Instrucciones del mensaje', source: 'Ver original',
    task: 'Seguir esta tarea', missing: 'Condiciones y datos que faltan', vocab: 'Palabras útiles',
    none: 'No se encontró una instrucción explícita.',
    when: 'Cuándo', where: 'Dónde', conditions: 'Condiciones', steps: 'Pasos',
  },
};

const SAMPLE_LABEL = {
  tech: 'Tech onboarding', ai: 'AI model report', finance: 'Finance operations', student: 'Student arrival',
};
const SAMPLE_FLAG = { tech: '🇨🇳', ai: '🇯🇵', finance: '🇪🇸', student: '🇺🇸' };

const ICON = {
  check: '<path d="m4.5 12.5 5 5 10-11"/>',
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
  alert: '<path d="M12 4 2.5 20h19Z"/><path d="M12 10v4"/><path d="M12 17.5h.01"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="m4.5 7.5 7.5 5.5 7.5-5.5"/>',
  bell: '<path d="M6.5 9.5a5.5 5.5 0 0 1 11 0c0 4 1.5 5.5 1.5 5.5H5s1.5-1.5 1.5-5.5Z"/><path d="M10 18.5a2 2 0 0 0 4 0"/>',
  pin: '<path d="M12 21s6.5-5.4 6.5-10.5a6.5 6.5 0 1 0-13 0C5.5 15.6 12 21 12 21Z"/><circle cx="12" cy="10.5" r="2.4"/>',
  list: '<path d="M8.5 6.5h11M8.5 12h11M8.5 17.5h11"/><path d="M4.5 6.5h.01M4.5 12h.01M4.5 17.5h.01"/>',
  quote: '<path d="M9.5 6.5C7 8 5.5 10 5.5 13v4.5H11V12H8.2c0-1.8.9-3 2.6-4.1Z"/><path d="M18.5 6.5C16 8 14.5 10 14.5 13v4.5H20V12h-2.8c0-1.8.9-3 2.6-4.1Z"/>',
  book: '<path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H10a2 2 0 0 1 2 2v13a2 2 0 0 0-2-2H4Z"/><path d="M20 5.5A1.5 1.5 0 0 0 18.5 4H14a2 2 0 0 0-2 2v13a2 2 0 0 1 2-2h6Z"/>',
  inbox: '<path d="M3.5 12.5 6 5.5h12l2.5 7v5a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2Z"/><path d="M3.5 12.5H9a3 3 0 0 0 6 0h5.5"/>',
  spark: '<path d="M12 3v3"/><path d="m5.6 5.6 2.1 2.1"/><path d="M3 12h3"/><path d="M18 12h3"/><path d="m16.3 7.7 2.1-2.1"/><path d="M12 21a7 7 0 0 0 0-14 7 7 0 0 0 0 14Z"/>',
  trash: '<path d="M4.5 7h15"/><path d="M9.5 7V5.5a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1V7"/><path d="M6.5 7l.8 12a1.5 1.5 0 0 0 1.5 1.4h6.4a1.5 1.5 0 0 0 1.5-1.4L17.5 7"/>',
  done: '<rect x="4" y="4.5" width="16" height="16" rx="3"/><path d="m8.5 12.5 2.5 2.5 4.8-5.4"/>',
};

function icon(name, cls) {
  return `<svg class="${cls || ''}" viewBox="0 0 24 24" fill="none" stroke="currentColor" ` +
    `stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[name]}</svg>`;
}

/* --------------------------------------------------------------------------
   State
   -------------------------------------------------------------------------- */
let config = {};
let samples = [];
let analysis = null;
let analysisText = '';
let analysisLanguage = 'en';
let draft = null;
let csrf = $('meta[name=csrf-token]').content;
let currentPage = 'understand';
let taskData = { tasks: [], server_time: Math.floor(Date.now() / 1000) };
let taskFilter = 'all';
let idleResultHTML = '';
let loadingTimer = null;

/* --------------------------------------------------------------------------
   Small helpers
   -------------------------------------------------------------------------- */
function node(tag, text, cls) {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = text;
  if (cls) n.className = cls;
  return n;
}
function html(tag, markup, cls) {
  const n = document.createElement(tag);
  if (markup !== undefined) n.innerHTML = markup;
  if (cls) n.className = cls;
  return n;
}
function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }

/** localStorage is unavailable in sandboxed frames — always degrade quietly. */
const store = {
  get(key) { try { return window.localStorage.getItem(key); } catch { return null; } },
  set(key, value) { try { window.localStorage.setItem(key, value); } catch { /* ignore */ } },
};

/* --------------------------------------------------------------------------
   Toasts
   -------------------------------------------------------------------------- */
function toast(text, kind = 'info') {
  const host = $('#global-message');
  const el = node('div', undefined, 'toast' + (kind === 'info' ? '' : ' toast--' + kind));
  el.append(html('span', icon(kind === 'error' ? 'alert' : kind === 'warn' ? 'alert' : 'check')));
  el.append(node('div', text, 'toast__text'));
  host.append(el);
  while (host.children.length > 3) host.firstElementChild.remove();
  const remove = () => {
    el.classList.add('is-leaving');
    el.addEventListener('animationend', () => el.remove(), { once: true });
    setTimeout(() => el.remove(), 600);
  };
  setTimeout(remove, kind === 'error' ? 8000 : 5000);
  el.addEventListener('click', remove);
}
/** Backwards-compatible alias used by handlers below. */
const message = (text) => toast(text);

/* --------------------------------------------------------------------------
   API wrapper
   -------------------------------------------------------------------------- */
async function api(path, method = 'GET', data) {
  const response = await fetch('/api' + path, {
    method,
    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
    body: data === undefined ? undefined : JSON.stringify(data),
  });
  let payload;
  try { payload = await response.json(); }
  catch { throw Error('The server returned an unexpected response. Check that it is running.'); }
  if (!response.ok) throw Error(payload.error || 'Request failed.');
  return payload;
}

/* --------------------------------------------------------------------------
   Theme
   -------------------------------------------------------------------------- */
function applyTheme(theme) {
  if (theme === 'light' || theme === 'dark') document.documentElement.dataset.theme = theme;
  else delete document.documentElement.dataset.theme;
  const dark = theme === 'dark' ||
    (!theme && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  const moon = $('.theme-icon--moon');
  const sun = $('.theme-icon--sun');
  if (moon) moon.hidden = dark;
  if (sun) sun.hidden = !dark;
}
$('#theme-toggle').addEventListener('click', () => {
  const current = store.get('bridge-theme');
  const isDark = current ? current === 'dark'
    : (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  const next = isDark ? 'light' : 'dark';
  store.set('bridge-theme', next);
  applyTheme(next);
});
applyTheme(store.get('bridge-theme'));

/* --------------------------------------------------------------------------
   Configuration banner + shell chrome
   -------------------------------------------------------------------------- */
function statusChip(label, kind, iconName) {
  const chip = node('span', undefined, 'chip-status' + (kind ? ' chip-status--' + kind : ''));
  if (iconName) chip.append(html('span', icon(iconName), 'chip-status__icon'));
  else chip.append(node('span', undefined, 'chip-status__dot'));
  chip.append(node('span', label));
  return chip;
}

async function refreshConfig() {
  config = await api('/config');
  csrf = config.csrf;

  const signedIn = Boolean(config.user);
  const label = $('#account-label');
  clear(label);
  if (signedIn) {
    label.className = 'account__who';
    const initials = (config.user.split('@')[0] || '?').slice(0, 2).toUpperCase();
    label.append(node('span', initials, 'account__avatar'));
    label.append(node('span', config.user, 'account__email'));
    label.title = 'Signed in as ' + config.user;
  } else {
    label.className = 'account__anon';
    label.append(html('span', icon('mail')));
    label.append(node('span', 'Not signed in'));
    label.title = 'Sign in to save tasks and receive reminders';
  }
  $('#sign-in').hidden = signedIn;
  $('#sign-out').hidden = !signedIn;

  const banner = $('#mode-banner');
  clear(banner);
  const aiLive = config.ai_mode !== 'demo';
  banner.append(statusChip(
    aiLive ? 'Live AI · ' + (config.ai_mode === 'gemini' ? 'Gemini' : 'OpenAI') : 'Prepared samples',
    aiLive ? 'live' : 'demo', aiLive ? 'spark' : null));
  const mailLive = config.mail_mode !== 'local';
  banner.append(statusChip(
    mailLive ? 'Real email delivery' : 'Local inbox only',
    mailLive ? 'live' : 'demo', mailLive ? 'mail' : null));

  $('#inbox-nav').hidden = config.mail_mode !== 'local';
  $('#local-worker').hidden = config.mail_mode !== 'local';
  $('#quick-times').hidden = config.mail_mode !== 'local';
  $('#consent-row').hidden = config.ai_mode === 'demo';
  $('#live-setup').hidden = config.ai_mode !== 'demo';

  const statusText = $('#custom-text-status-text');
  statusText.textContent = config.ai_mode === 'demo'
    ? 'Offline demo mode: you can paste text, but only unchanged examples can be explained until live AI is connected.'
    : 'Live processing is ready. Paste your own text and choose the languages below.';
  $('#custom-text-status').className = 'notice ' + (config.ai_mode === 'demo' ? 'notice--warn' : 'notice--ok');
}

/* --------------------------------------------------------------------------
   Navigation
   -------------------------------------------------------------------------- */
async function showPage(page) {
  currentPage = page;
  ['understand', 'tasks', 'inbox'].forEach((p) => { $('#page-' + p).hidden = p !== page; });
  $$('nav button').forEach((b) => {
    if (b.dataset.page === page) b.setAttribute('aria-current', 'page');
    else b.removeAttribute('aria-current');
  });
  if (page === 'tasks') await loadTasks();
  if (page === 'inbox') await loadInbox();
}
/* --------------------------------------------------------------------------
   Understand page — example cards, counter, analysis
   -------------------------------------------------------------------------- */
function renderExamples() {
  const host = $('#examples');
  clear(host);
  samples.forEach((sample) => {
    const card = node('button', undefined, 'example-card');
    card.type = 'button';
    card.dataset.sample = sample.id;
    card.append(node('span', SAMPLE_FLAG[sample.id] || '🌐', 'example-card__flag'));
    card.append(node('span', SAMPLE_LABEL[sample.id] || sample.title, 'example-card__name'));
    card.append(node('span', LANGUAGES[sample.language] + ' source · ' + sample.title, 'example-card__meta'));
    card.addEventListener('click', () => loadExample(sample));
    host.append(card);
  });
}

function loadExample(sample) {
  if ($('#source-input').value.trim() && $('#source-input').value !== sample.text &&
      !confirm('Replace the text in the message box with this example?')) return;
  $('#source-input').value = sample.text;
  $('#document-title').value = sample.title;
  $('#input-language').value = sample.language;
  $('#analysis-error').textContent = '';
  $$('.example-card').forEach((c) => c.classList.toggle('is-active', c.dataset.sample === sample.id));
  updateCounter();
  resetAnalysis();
  toast('Example loaded — you can change the output language independently.');
  $('#source-input').scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function updateCounter() {
  const value = $('#source-input').value;
  const count = $('#char-count');
  count.textContent = value.length.toLocaleString();
  count.parentElement.classList.toggle('is-warn', value.length > 11000);
  $('#clear-text').disabled = value.trim() === '';
}

function renderIdleResult() {
  const result = $('#result');
  if (idleResultHTML) result.innerHTML = idleResultHTML;
}

function resetAnalysis() {
  analysis = null;
  draft = null;
  $('#evidence-panel').hidden = true;
  renderIdleResult();
}

function startLoading() {
  const result = $('#result');
  result.removeAttribute('lang');
  const steps = ['Reading the original text', 'Identifying instructions', 'Checking for missing details', 'Writing the plain-language summary'];
  const wrap = node('div', undefined, 'stack-sm');
  wrap.append(node('div', undefined, 'skeleton skeleton--title'));
  wrap.append(node('div', undefined, 'skeleton skeleton--line'));
  wrap.append(node('div', undefined, 'skeleton skeleton--line'));
  wrap.append(node('div', undefined, 'skeleton skeleton--block'));
  const list = node('div', undefined, 'loader-steps');
  const rows = steps.map((text) => {
    const row = node('div', undefined, 'loader-step');
    row.append(node('span', undefined, 'loader-step__dot'));
    row.append(node('span', text));
    list.append(row);
    return row;
  });
  wrap.append(list);
  wrap.append(node('div', undefined, 'skeleton skeleton--card'));
  clear(result);
  result.append(wrap);
  let i = 0;
  rows[0].classList.add('is-on');
  loadingTimer = setInterval(() => {
    if (i < rows.length - 1) { rows[i].classList.remove('is-on'); i += 1; rows[i].classList.add('is-on'); }
  }, 620);
}
function stopLoading() {
  if (loadingTimer) { clearInterval(loadingTimer); loadingTimer = null; }
}

/* ---- Evidence viewer ---- */
function showEvidence(quote) {
  const panel = $('#evidence-panel');
  const area = $('#evidence');
  clear(area);
  const start = analysisText.indexOf(quote);
  if (start < 0) { toast('That passage could not be located in the current text.', 'warn'); return; }
  area.append(document.createTextNode(analysisText.slice(0, start)));
  area.append(node('mark', quote));
  area.append(document.createTextNode(analysisText.slice(start + quote.length)));
  panel.hidden = false;
  panel.open = true;
  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/* ---- Result rendering ---- */
function detailText(value) {
  const t = typeof value === 'string' ? value.trim() : '';
  if (/^(none|null|n\/a|not applicable|无|無|なし|該当なし|ninguno|ninguna|no aplica)[.。]?$/i.test(t)) return '';
  return t;
}

function metaRow(iconName, label, text) {
  const row = node('div', undefined, 'meta-row');
  row.append(html('span', icon(iconName)));
  const body = node('span');
  body.append(node('b', label + ': '));
  body.append(document.createTextNode(text));
  row.append(body);
  return row;
}

function actionCard(action, labels, index) {
  const card = node('article', undefined, 'action-card');

  const top = node('div', undefined, 'action-card__top');
  top.append(node('span', String(index + 1).padStart(2, '0'), 'action-card__index'));
  top.append(node('h4', action.title, 'action-card__title'));
  card.append(top);

  const meta = node('div', undefined, 'action-card__meta');
  const when = detailText(action.deadline_text);
  const where = detailText(action.location);
  const conditions = detailText(action.conditions);
  if (when) meta.append(metaRow('clock', labels.when, when));
  if (where) meta.append(metaRow('pin', labels.where, where));
  if (conditions) meta.append(metaRow('alert', labels.conditions, conditions));
  const steps = (action.steps || []).map(detailText).filter(Boolean);
  if (steps.length) {
    meta.append(metaRow('list', labels.steps, ''));
    const list = node('ul', undefined, 'action-card__steps');
    steps.forEach((step) => list.append(node('li', step)));
    meta.append(list);
  }
  if (meta.childElementCount) card.append(meta);

  const foot = node('div', undefined, 'action-card__foot');
  const sourceBtn = node('button', undefined, 'btn btn--sm');
  sourceBtn.type = 'button';
  sourceBtn.innerHTML = icon('book') + '<span>' + labels.source + '</span>';
  sourceBtn.addEventListener('click', () => showEvidence(action.source_quote));
  const taskBtn = node('button', undefined, 'btn btn--sm btn--primary');
  taskBtn.type = 'button';
  taskBtn.innerHTML = icon('check') + '<span>' + labels.task + '</span>';
  taskBtn.addEventListener('click', () => openTask(action));
  foot.append(sourceBtn, taskBtn);
  card.append(foot);
  return card;
}

function renderAnalysis() {
  const result = $('#result');
  const labels = WORDS[analysisLanguage] || WORDS.en;
  result.lang = analysisLanguage;
  clear(result);

  const meta = node('div', undefined, 'translation-meta');
  meta.append(html('span', '<span class="pill pill--brand">' + LANGUAGES[analysisLanguage] + '</span>'));
  meta.append(node('span', 'Translated from ' + (LANGUAGES[analysis.source_language] || analysis.source_language) + ' · review the original before acting'));
  result.append(meta);

  const meaning = node('div', undefined, 'meaning-card');
  const meaningLabel = node('div', undefined, 'meaning-card__label');
  meaningLabel.innerHTML = icon('quote') + '<span>' + labels.meaning + '</span>';
  meaning.append(meaningLabel);
  meaning.append(node('p', analysis.summary, 'meaning-card__text'));
  result.append(meaning);

  const actionsTitle = node('h3', undefined, 'section-title');
  actionsTitle.append(node('span', labels.actions));
  actionsTitle.append(node('span', String(analysis.actions.length), 'section-title__count'));
  result.append(actionsTitle);

  if (!analysis.actions.length) {
    const empty = node('div', undefined, 'notice');
    empty.innerHTML = icon('alert');
    empty.append(node('span', labels.none));
    result.append(empty);
  }
  analysis.actions.forEach((action, i) => result.append(actionCard(action, labels, i)));

  const missing = (analysis.missing_information || []).map(detailText).filter(Boolean);
  if (missing.length) {
    const title = node('h3', undefined, 'section-title');
    title.append(node('span', labels.missing));
    result.append(title);
    missing.forEach((item) => {
      const box = node('div', undefined, 'notice notice--warn');
      box.innerHTML = icon('alert');
      box.append(node('span', item));
      result.append(box);
    });
  }

  if (analysis.words && analysis.words.length) {
    const title = node('h3', undefined, 'section-title');
    title.append(node('span', labels.vocab));
    result.append(title);
    const dl = node('dl', undefined, 'vocab-grid');
    analysis.words.forEach((word) => {
      const item = node('div', undefined, 'vocab-item');
      item.append(node('dt', word.term));
      item.append(node('dd', word.meaning));
      dl.append(item);
    });
    result.append(dl);
  }
}

/* --------------------------------------------------------------------------
   Task dialog
   -------------------------------------------------------------------------- */
function openTask(action) {
  draft = action;
  $('#task-title').value = action.title;
  const box = $('#draft-condition');
  clear(box);
  const bits = [];
  const conditions = detailText(action.conditions);
  const when = detailText(action.deadline_text);
  const where = detailText(action.location);
  if (conditions) bits.push('Conditions: ' + conditions);
  if (when) bits.push('Stated in the source: ' + when);
  if (where) bits.push('Location: ' + where);
  const steps = (action.steps || []).map(detailText).filter(Boolean);
  if (steps.length) bits.push('Steps: ' + steps.join(' · '));
  if (bits.length) {
    const notice = node('div', undefined, 'notice notice--info');
    notice.innerHTML = icon('alert');
    notice.append(node('span', bits.join('\n')));
    notice.lastElementChild.classList.add('notice__body');
    box.append(notice);
  }
  $('#deadline-hint').innerHTML = '';
  $('#deadline-hint').append(html('span', icon('clock')));
  $('#deadline-hint').append(node('span', 'Enter and confirm the deadline, reminder time, and time zone. A source event time is not automatically a deadline.'));
  $('#task-feedback').textContent = '';
  $('#confirmed').checked = false;
  $('#due').value = '';
  $('#remind').value = '';
  $('#task-dialog').showModal();
}

function formatted(ts, zone, language = 'en') {
  try {
    return new Intl.DateTimeFormat(language, { timeZone: zone, dateStyle: 'medium', timeStyle: 'short' }).format(ts * 1000) + ' · ' + zone;
  } catch {
    return new Date(ts * 1000).toLocaleString();
  }
}

function localInput(date, zone) {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: zone, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(date);
  const p = Object.fromEntries(parts.map((x) => [x.type, x.value]));
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`;
}

/* --------------------------------------------------------------------------
   Tasks page
   -------------------------------------------------------------------------- */
function relativeLabel(seconds) {
  const abs = Math.abs(seconds);
  if (abs < 60) return { text: 'less than a minute', strong: false };
  const units = [['day', 86400], ['hour', 3600], ['minute', 60]];
  for (const [name, size] of units) {
    if (abs >= size) {
      const n = Math.floor(abs / size);
      const plural = n === 1 ? name : name + 's';
      return { text: n + ' ' + plural, strong: true };
    }
  }
  return { text: Math.floor(abs / 60) + ' minutes', strong: true };
}

function countdownPill(task, now) {
  if (task.status === 'done') {
    const pill = node('span', undefined, 'pill pill--ok');
    pill.innerHTML = icon('check') + '<span>Done · confirmed by you</span>';
    return pill;
  }
  const diff = task.due_at - now;
  const rel = relativeLabel(diff);
  if (diff < 0) {
    const pill = node('span', undefined, 'pill pill--danger');
    pill.innerHTML = icon('alert') + '<span>Overdue by ' + rel.text + '</span>';
    return pill;
  }
  const soon = diff <= 48 * 3600;
  const pill = node('span', undefined, 'pill' + (soon ? ' pill--warn' : ' pill--brand'));
  pill.innerHTML = icon('clock') + '<span>Due in ' + rel.text + '</span>';
  return pill;
}

function reminderPill(task) {
  const map = {
    pending: ['Reminder scheduled', 'pill--brand', 'bell'],
    sent: ['Reminder sent', 'pill--ok', 'check'],
    failed: ['Reminder failed', 'pill--danger', 'alert'],
    canceled: ['Reminder canceled', '', 'bell'],
  };
  const [label, cls, iconName] = map[task.reminder_status] || ['Reminder', '', 'bell'];
  const pill = node('span', undefined, 'pill ' + cls);
  pill.innerHTML = icon(iconName) + '<span>' + label + '</span>';
  return pill;
}

function taskDetailRows(task, labels) {
  const details = task.details || {};
  const rows = node('div', undefined, 'detail-list');
  const map = [['deadline_text', labels.when], ['location', labels.where], ['conditions', labels.conditions]];
  map.forEach(([key, label]) => {
    const value = detailText(details[key]);
    if (!value) return;
    const row = node('div', undefined, 'detail-row');
    row.append(node('b', label));
    row.append(node('span', value));
    rows.append(row);
  });
  const steps = (details.steps || []).map(detailText).filter(Boolean);
  if (steps.length) {
    const row = node('div', undefined, 'detail-row');
    row.append(node('b', labels.steps));
    const list = node('ul', undefined, 'detail-steps');
    steps.forEach((step) => list.append(node('li', step)));
    row.append(list);
    rows.append(row);
  }
  return rows.childElementCount ? rows : null;
}

function taskCard(task, now, highlight) {
  const done = task.status === 'done';
  const overdue = !done && task.due_at < now;
  const soon = !done && !overdue && (task.due_at - now) <= 48 * 3600;
  const card = node('article', undefined,
    'task-card' + (done ? ' task-card--done is-done' : overdue ? ' task-card--overdue' : soon ? ' task-card--soon' : ''));
  card.id = 'task-' + task.id;
  if (task.id === highlight) card.classList.add('selected');

  const head = node('div', undefined, 'task-card__head');
  head.append(node('h3', task.title, 'task-card__title'));
  const badges = node('div', undefined, 'task-card__badges');
  badges.append(countdownPill(task, now));
  badges.append(reminderPill(task));
  head.append(badges);
  card.append(head);

  const meta = node('div', undefined, 'task-card__meta');
  const deadline = node('div', undefined, 'task-meta');
  const dLabel = node('div', undefined, 'task-meta__label');
  dLabel.innerHTML = icon('clock') + '<span>Deadline</span>';
  deadline.append(dLabel);
  deadline.append(node('div', formatted(task.due_at, task.timezone, task.language), 'task-meta__value'));
  const rel = relativeLabel(task.due_at - now);
  const sub = done ? 'Completed' : (task.due_at < now ? 'Passed ' + rel.text + ' ago' : 'In ' + rel.text);
  deadline.append(node('div', sub, 'task-meta__sub'));
  meta.append(deadline);

  const remind = node('div', undefined, 'task-meta');
  const rLabel = node('div', undefined, 'task-meta__label');
  rLabel.innerHTML = icon('bell') + '<span>Reminder</span>';
  remind.append(rLabel);
  remind.append(node('div', formatted(task.remind_at, task.timezone, task.language), 'task-meta__value'));
  remind.append(node('div', 'Source: ' + (task.source_title || 'Untitled'), 'task-meta__sub'));
  meta.append(remind);
  card.append(meta);

  const rows = taskDetailRows(task, WORDS[task.language] || WORDS.en);
  if (rows) card.append(rows);

  if (task.last_error) {
    const warn = node('div', undefined, 'notice notice--warn mt-1');
    warn.innerHTML = icon('alert');
    warn.append(node('span', task.last_error));
    card.append(warn);
  }

  const foot = node('div', undefined, 'task-card__foot');
  foot.append(node('span', task.provenance || 'Deadline entered and confirmed by user', 'quiet grow'));
  if (!done) {
    const doneBtn = node('button', undefined, 'btn btn--sm');
    doneBtn.type = 'button';
    doneBtn.innerHTML = icon('done') + '<span>Mark as done</span>';
    doneBtn.addEventListener('click', async () => {
      if (!confirm('Have you completed this instruction outside BRIDGE?')) return;
      doneBtn.disabled = true;
      try {
        await api('/tasks/' + task.id + '/complete', 'POST', { confirmed: true });
        toast('Task marked done. Any pending reminder was canceled.');
        await loadTasks();
      } catch (e) { toast(e.message, 'error'); doneBtn.disabled = false; }
    });
    foot.append(doneBtn);
  }
  const delBtn = node('button', undefined, 'btn btn--sm btn--danger');
  delBtn.type = 'button';
  delBtn.innerHTML = icon('trash') + '<span>Delete</span>';
  delBtn.addEventListener('click', async () => {
    if (!confirm('Delete this task and cancel any pending reminder? Previously sent emails cannot be removed.')) return;
    delBtn.disabled = true;
    try { await api('/tasks/' + task.id, 'DELETE'); toast('Task deleted.'); await loadTasks(); }
    catch (e) { toast(e.message, 'error'); delBtn.disabled = false; }
  });
  foot.append(delBtn);
  card.append(foot);
  return card;
}

function setStat(id, value) { const el = $(id); if (el) el.textContent = String(value); }

async function loadTasks() {
  await refreshConfig();
  const area = $('#tasks');
  clear(area);
  $('#task-stats').hidden = true;
  $('#task-toolbar').hidden = true;

  if (!config.user) {
    const empty = node('div', undefined, 'empty');
    empty.append(html('div', icon('inbox'), 'empty__art empty__art--icon'));
    empty.append(node('p', 'Sign in to view and save your tasks', 'empty__title'));
    empty.append(node('p', 'Tasks are tied to your email so reminders reach the right person. Sign-in uses a one-time link — no password.', 'empty__text'));
    const actions = node('div', undefined, 'empty__actions');
    const signIn = node('button', 'Email sign-in', 'btn btn--primary');
    signIn.type = 'button';
    signIn.addEventListener('click', () => $('#auth-dialog').showModal());
    actions.append(signIn);
    empty.append(actions);
    area.append(empty);
    setStat('#task-count', '');
    return;
  }

  taskData = await api('/tasks');
  const tasks = taskData.tasks;
  const now = taskData.server_time;
  setStat('#task-count', tasks.length);

  const open = tasks.filter((t) => t.status !== 'done');
  const done = tasks.filter((t) => t.status === 'done');
  const soonList = open.filter((t) => t.due_at >= now && (t.due_at - now) <= 48 * 3600);
  const overdue = open.filter((t) => t.due_at < now);

  if (!tasks.length) {
    const empty = node('div', undefined, 'empty');
    empty.append(html('div', icon('inbox'), 'empty__art empty__art--icon'));
    empty.append(node('p', 'No saved tasks yet', 'empty__title'));
    empty.append(node('p', 'Explain a message, then choose “Track this task” on an instruction to save it with a deadline and reminder.', 'empty__text'));
    const actions = node('div', undefined, 'empty__actions');
    const go = node('button', 'Explain a message', 'btn btn--primary');
    go.type = 'button';
    go.addEventListener('click', () => { location.hash = 'understand'; showPage('understand'); });
    actions.append(go);
    empty.append(actions);
    area.append(empty);
    return;
  }

  $('#task-stats').hidden = false;
  $('#task-toolbar').hidden = false;
  setStat('#stat-total', tasks.length);
  setStat('#stat-open', open.length);
  setStat('#stat-soon', soonList.length + overdue.length);
  setStat('#stat-done', done.length);

  const visible = taskFilter === 'open' ? open : taskFilter === 'done' ? done : tasks;
  $('#task-summary').textContent = visible.length + ' of ' + tasks.length + ' shown' +
    (overdue.length ? ' · ' + overdue.length + ' overdue' : '');

  if (!visible.length) {
    const empty = node('div', undefined, 'empty empty--plain');
    empty.append(node('p', taskFilter === 'done' ? 'Nothing completed yet' : 'Nothing open right now', 'empty__title'));
    empty.append(node('p', taskFilter === 'done'
      ? 'Tasks you confirm as done will collect here.'
      : 'Every saved task has been confirmed complete. Nice work.', 'empty__text'));
    area.append(empty);
    return;
  }

  const highlight = location.hash.startsWith('#task=') ? location.hash.slice(6) : null;
  visible.forEach((task) => area.append(taskCard(task, now, highlight)));
}

/* --------------------------------------------------------------------------
   Inbox page
   -------------------------------------------------------------------------- */
async function loadInbox() {
  if (config.mail_mode !== 'local') return;
  const { messages } = await api('/inbox');
  const list = $('#mail-list');
  clear(list);
  $('#inbox-count').textContent = messages.length
    ? messages.length + (messages.length === 1 ? ' message' : ' messages') + ' · local only'
    : 'No messages yet';

  if (!messages.length) {
    const empty = node('div', undefined, 'empty empty--plain');
    empty.append(html('div', icon('mail'), 'empty__art empty__art--icon'));
    empty.append(node('p', 'Inbox is empty', 'empty__title'));
    empty.append(node('p', 'Request a sign-in link or wait for a due reminder — either one lands here instead of being sent for real.', 'empty__text'));
    list.append(empty);
    return;
  }

  messages.forEach((mail, index) => {
    const item = node('button', undefined, 'mail-item');
    item.type = 'button';
    const top = node('div', undefined, 'mail-item__top');
    top.append(html('span', icon(mail.kind === 'login' ? 'check' : 'bell'), 'mail-item__icon'));
    top.append(node('span', mail.subject, 'mail-item__subject'));
    if (index === 0) top.append(node('span', undefined, 'mail-item__dot'));
    item.append(top);
    const meta = node('div', undefined, 'mail-item__meta');
    meta.append(node('span', mail.recipient));
    meta.append(node('span', '·'));
    meta.append(node('span', new Date(mail.created_at * 1000).toLocaleString()));
    item.append(meta);
    item.addEventListener('click', () => {
      $$('.mail-item').forEach((el) => el.classList.remove('is-active'));
      item.classList.add('is-active');
      openMail(mail);
    });
    list.append(item);
  });

  const first = list.querySelector('.mail-item');
  if (first) first.click();
}

function openMail(mail) {
  const view = $('#mail-view');
  clear(view);
  const chrome = node('div', undefined, 'mail-view__chrome');
  chrome.innerHTML = '<span class="mail-view__dots" aria-hidden="true"><i></i><i></i><i></i></span>' +
    '<span class="mail-view__title">Local delivery preview · not sent</span>';
  view.append(chrome);

  const body = node('div', undefined, 'mail-view__body');
  const header = node('div', undefined, 'mail-header');
  header.append(node('span', 'Local email · never sent', 'eyebrow'));
  header.append(node('h2', mail.subject));
  const meta = node('div', undefined, 'mail-meta');
  const to = node('div');
  to.append(node('b', 'To'));
  to.append(document.createTextNode(' ' + mail.recipient));
  const when = node('div');
  when.append(node('b', 'Created'));
  when.append(document.createTextNode(' ' + new Date(mail.created_at * 1000).toLocaleString()));
  meta.append(to, when);
  header.append(meta);
  body.append(header);
  body.append(node('div', mail.body, 'mail-body'));

  const actions = node('div', undefined, 'row mt-3');
  if (mail.kind === 'login') {
    const btn = node('button', undefined, 'btn btn--primary');
    btn.type = 'button';
    btn.innerHTML = icon('check') + '<span>Open local sign-in link</span>';
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      try {
        const token = new URL(mail.action_url).searchParams.get('token');
        const data = await api('/auth/local-confirm', 'POST', { token });
        csrf = data.csrf;
        await refreshConfig();
        toast('Signed in locally. This simulates email ownership verification.');
        await showPage('tasks');
        if (draft) $('#task-dialog').showModal();
      } catch (e) { toast(e.message, 'error'); btn.disabled = false; }
    });
    actions.append(btn);
  } else {
    const btn = node('button', undefined, 'btn');
    btn.type = 'button';
    btn.innerHTML = icon('inbox') + '<span>View task</span>';
    btn.addEventListener('click', async () => {
      location.hash = new URL(mail.action_url).hash;
      await showPage('tasks');
    });
    actions.append(btn);
  }
  body.append(actions);
  view.append(body);
}

/* --------------------------------------------------------------------------
   Wiring
   -------------------------------------------------------------------------- */
$$('nav button').forEach((b) => {
  b.addEventListener('click', () => {
    location.hash = b.dataset.page;
    showPage(b.dataset.page).catch((e) => toast(e.message, 'error'));
  });
});

$('#source-input').addEventListener('input', () => {
  $('#analysis-error').textContent = '';
  resetAnalysis();
  updateCounter();
});
$('#source-input').addEventListener('paste', () => {
  $('#input-language').value = 'auto';
  $$('.example-card').forEach((c) => c.classList.remove('is-active'));
});
$('#source-input').addEventListener('keydown', (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') { event.preventDefault(); $('#analyze').click(); }
});
$('#clear-text').addEventListener('click', () => {
  $('#source-input').value = '';
  updateCounter();
  resetAnalysis();
  $('#source-input').focus();
});
$('#language').addEventListener('change', resetAnalysis);
$('#input-language').addEventListener('change', resetAnalysis);

$('#analyze').addEventListener('click', async () => {
  const button = $('#analyze');
  const input = $('#source-input').value;
  const lang = $('#language').value;
  const inputLang = $('#input-language').value;
  if (!input.trim()) { toast('Paste a message first, or load one of the examples above.', 'warn'); $('#source-input').focus(); return; }

  button.disabled = true;
  button.innerHTML = '<span class="btn__spinner"></span><span>Explaining…</span>';
  $('#analysis-error').textContent = '';
  // Only reveal the loading state if the request is not instant: in offline
  // demo mode the answer returns immediately and a skeleton flash reads as a bug.
  const loadingDelay = setTimeout(startLoading, 160);
  try {
    if (config.ai_mode === 'demo' && !samples.some((s) => s.text === input.trim())) {
      clearTimeout(loadingDelay);
      stopLoading();
      $('#live-setup').open = true;
      throw Error('Your text is accepted, but live AI is not connected. Follow “Enable processing for your own text” above, or load an unchanged example.');
    }
    const data = await api('/analyze', 'POST', {
      text: input, language: lang, input_language: inputLang, consent: $('#consent').checked,
    });
    clearTimeout(loadingDelay);
    if ($('#source-input').value !== input || $('#language').value !== lang || $('#input-language').value !== inputLang) {
      stopLoading();
      resetAnalysis();
      toast('The input changed during processing. Please explain it again.', 'warn');
      return;
    }
    stopLoading();
    analysis = data.result;
    analysisText = input.trim();
    analysisLanguage = lang;
    renderAnalysis();
    if (window.matchMedia && window.matchMedia('(max-width:1080px)').matches) {
      $('#result-title').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    toast('Explanation ready · ' + analysis.actions.length + ' instruction' + (analysis.actions.length === 1 ? '' : 's') + ' found.');
  } catch (e) {
    clearTimeout(loadingDelay);
    stopLoading();
    resetAnalysis();
    $('#analysis-error').textContent = e.message;
    toast(e.message, 'error');
  } finally {
    button.disabled = false;
    button.innerHTML = '<span>Explain this message</span>' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15"/><path d="m13 6 6 6-6 6"/></svg>';
  }
});

$('#sign-in').addEventListener('click', () => $('#auth-dialog').showModal());
$('#close-auth').addEventListener('click', () => $('#auth-dialog').close());
$('#close-task').addEventListener('click', () => $('#task-dialog').close());

$('#auth-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  $('#auth-feedback').textContent = '';
  try {
    const result = await api('/auth/request', 'POST', { email: $('#email').value });
    toast(result.message);
    if (config.mail_mode === 'local') { $('#auth-dialog').close(); await showPage('inbox'); }
  } catch (err) {
    $('#auth-feedback').textContent = err.message;
    toast(err.message, 'error');
  } finally { button.disabled = false; }
});

$('#sign-out').addEventListener('click', async () => {
  try {
    await api('/auth/logout', 'POST', {});
    await refreshConfig();
    setStat('#task-count', '');
    clear($('#tasks'));
    clear($('#mail-list'));
    $('#inbox-count').textContent = 'No messages yet';
    toast('Signed out.');
    await showPage('understand');
  } catch (e) { toast(e.message, 'error'); }
});

$('#task-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = event.submitter;
  button.disabled = true;
  $('#task-feedback').textContent = '';
  try {
    await refreshConfig();
    if (!config.user) {
      $('#task-dialog').close();
      $('#auth-dialog').showModal();
      $('#auth-feedback').textContent = 'Sign in first. Your draft stays in this tab.';
      return;
    }
    await api('/tasks', 'POST', {
      title: $('#task-title').value,
      language: analysisLanguage,
      due_local: $('#due').value,
      remind_local: $('#remind').value,
      timezone: $('#zone').value,
      source_title: $('#document-title').value,
      details: {
        steps: draft?.steps || [],
        location: draft?.location || '',
        deadline_text: draft?.deadline_text || '',
        conditions: draft?.conditions || '',
      },
      confirmed: $('#confirmed').checked,
    });
    draft = null;
    $('#task-dialog').close();
    await showPage('tasks');
    toast('Task saved. Keep the reminder worker running for scheduled delivery.');
  } catch (err) {
    $('#task-feedback').textContent = err.message;
  } finally { button.disabled = false; }
});

$('#quick-times').addEventListener('click', () => {
  const now = Date.now(); const minute = 60000;
  const zone = $('#zone').value;
  $('#remind').value = localInput(new Date(Math.ceil(now / minute) * minute + minute), zone);
  $('#due').value = localInput(new Date(Math.ceil(now / minute) * minute + 10 * minute), zone);
  $('#deadline-hint').innerHTML = '';
  $('#deadline-hint').append(html('span', icon('alert')));
  $('#deadline-hint').append(node('span', 'Quick-test dates chosen by you. These are NOT deadlines extracted from the document.'));
});

$('#refresh-tasks').addEventListener('click', () => loadTasks().catch((e) => toast(e.message, 'error')));
$('#refresh-inbox').addEventListener('click', () => loadInbox().catch((e) => toast(e.message, 'error')));
$('#check-due').addEventListener('click', async () => {
  const button = $('#check-due');
  button.disabled = true;
  try {
    const result = await api('/local/run-reminders', 'POST', {});
    $('#worker-status').textContent = result.sent + ' due reminder(s) placed in the local inbox.';
    toast(result.sent + ' due reminder(s) delivered to the local inbox.');
    await loadTasks();
  } catch (e) { toast(e.message, 'error'); } finally { button.disabled = false; }
});

$$('#task-toolbar .segmented button').forEach((button) => {
  button.addEventListener('click', () => {
    taskFilter = button.dataset.filter;
    $$('#task-toolbar .segmented button').forEach((b) => b.setAttribute('aria-pressed', String(b === button)));
    renderTaskList();
  });
});

function renderTaskList() {
  const area = $('#tasks');
  const tasks = taskData.tasks || [];
  const now = taskData.server_time;
  if (!tasks.length) return;
  const open = tasks.filter((t) => t.status !== 'done');
  const done = tasks.filter((t) => t.status === 'done');
  const overdue = open.filter((t) => t.due_at < now);
  const visible = taskFilter === 'open' ? open : taskFilter === 'done' ? done : tasks;
  clear(area);
  $('#task-summary').textContent = visible.length + ' of ' + tasks.length + ' shown' +
    (overdue.length ? ' · ' + overdue.length + ' overdue' : '');
  if (!visible.length) {
    const empty = node('div', undefined, 'empty empty--plain');
    empty.append(node('p', taskFilter === 'done' ? 'Nothing completed yet' : 'Nothing open right now', 'empty__title'));
    empty.append(node('p', taskFilter === 'done'
      ? 'Tasks you confirm as done will collect here.'
      : 'Every saved task has been confirmed complete. Nice work.', 'empty__text'));
    area.append(empty);
    return;
  }
  const highlight = location.hash.startsWith('#task=') ? location.hash.slice(6) : null;
  visible.forEach((task) => area.append(taskCard(task, now, highlight)));
}

window.addEventListener('hashchange', () => {
  const hash = location.hash.slice(1);
  showPage(hash.startsWith('task=') ? 'tasks' : ['tasks', 'inbox'].includes(hash) ? hash : 'understand')
    .catch((e) => toast(e.message, 'error'));
});
window.addEventListener('focus', () => refreshConfig().catch(() => {}));

/* --------------------------------------------------------------------------
   Boot
   -------------------------------------------------------------------------- */
(async () => {
  idleResultHTML = $('#result').innerHTML;
  updateCounter();
  await refreshConfig();
  const data = await api('/samples');
  samples = data.samples;
  renderExamples();
  const hash = location.hash.slice(1);
  await showPage(hash.startsWith('task=') ? 'tasks' : ['tasks', 'inbox'].includes(hash) ? hash : 'understand');

  // Deep link straight to a task by loading the tasks page once signed in.
  if (hash.startsWith('task=') && config.user) {
    const target = document.getElementById('task-' + hash.slice(6));
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
})().catch((e) => toast(e.message, 'error'));
