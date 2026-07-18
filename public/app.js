const authView = document.querySelector('#auth-view');
const dashboardView = document.querySelector('#dashboard-view');
const form = document.querySelector('#account-form');
const loginTab = document.querySelector('#login-tab');
const registerTab = document.querySelector('#register-tab');
const submitButton = document.querySelector('#submit-button');
const formError = document.querySelector('#form-error');
const usernameHint = document.querySelector('#username-hint');
const passwordInput = document.querySelector('#password');
const keyList = document.querySelector('#key-list');
const newKeyPanel = document.querySelector('#new-key');
const newKeyValue = document.querySelector('#new-key-value');
const toast = document.querySelector('#toast');
let mode = 'login';

function setMode(nextMode) {
  mode = nextMode;
  const registering = mode === 'register';
  loginTab.setAttribute('aria-selected', String(!registering));
  registerTab.setAttribute('aria-selected', String(registering));
  submitButton.textContent = registering ? '建立帳號' : '登入';
  passwordInput.autocomplete = registering ? 'new-password' : 'current-password';
  usernameHint.classList.toggle('hidden', !registering);
  formError.textContent = '';
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.remove('hidden');
  window.setTimeout(() => toast.classList.add('hidden'), 2400);
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.message?.detail || '請求失敗，請稍後重試。');
  return body;
}

function formatDate(value) {
  if (!value) return '尚未使用';
  return new Intl.DateTimeFormat('zh-TW', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
}

function renderKeys(keys) {
  keyList.replaceChildren();
  if (!keys.length) {
    const empty = document.createElement('p');
    empty.className = 'empty';
    empty.textContent = '尚未建立任何 API Key。';
    keyList.append(empty);
    return;
  }
  for (const key of keys) {
    const row = document.createElement('div');
    row.className = 'key-row';
    const value = document.createElement('code');
    value.textContent = key.display;
    const created = document.createElement('span');
    created.textContent = `建立於 ${formatDate(key.created_at)}`;
    const used = document.createElement('span');
    used.textContent = key.last_used_at ? `最近使用 ${formatDate(key.last_used_at)}` : '尚未使用';
    row.append(value, created, used);
    keyList.append(row);
  }
}

async function loadAccount() {
  try {
    const body = await request('/api/me');
    document.querySelector('#current-user').textContent = body.message.username;
    renderKeys(body.message.keys);
    authView.classList.add('hidden');
    dashboardView.classList.remove('hidden');
  } catch {
    dashboardView.classList.add('hidden');
    authView.classList.remove('hidden');
  }
}

loginTab.addEventListener('click', () => setMode('login'));
registerTab.addEventListener('click', () => setMode('register'));

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  formError.textContent = '';
  submitButton.disabled = true;
  const data = Object.fromEntries(new FormData(form));
  try {
    await request(`/api/${mode}`, { method: 'POST', body: JSON.stringify(data) });
    if (mode === 'register') {
      await request('/api/login', { method: 'POST', body: JSON.stringify(data) });
      showToast('帳號已建立');
    }
    form.reset();
    await loadAccount();
  } catch (error) {
    formError.textContent = error.message;
  } finally {
    submitButton.disabled = false;
  }
});

document.querySelector('#create-key-button').addEventListener('click', async (event) => {
  event.currentTarget.disabled = true;
  try {
    const body = await request('/api/keys', { method: 'POST' });
    newKeyValue.textContent = body.message.api_key;
    newKeyPanel.classList.remove('hidden');
    await loadAccount();
  } catch (error) {
    showToast(error.message);
  } finally {
    event.currentTarget.disabled = false;
  }
});

document.querySelector('#copy-key-button').addEventListener('click', async () => {
  await navigator.clipboard.writeText(newKeyValue.textContent);
  showToast('API Key 已複製');
});

document.querySelector('#logout-button').addEventListener('click', async () => {
  try {
    await request('/api/logout', { method: 'POST' });
  } finally {
    newKeyPanel.classList.add('hidden');
    await loadAccount();
  }
});

loadAccount();

