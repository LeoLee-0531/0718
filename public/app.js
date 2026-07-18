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
const newKeyDialog = document.querySelector('#new-key');
const newKeyValue = document.querySelector('#new-key-value');
const newKeyStatus = document.querySelector('#new-key-status');
const toast = document.querySelector('#toast');
const keyNameDialog = document.querySelector('#key-name-dialog');
const keyNameForm = document.querySelector('#key-name-form');
const keyNameInput = document.querySelector('#key-name-input');
const keyNameError = document.querySelector('#key-name-error');
const keyNameSubmit = document.querySelector('#key-name-submit');
const removeKeyDialog = document.querySelector('#remove-key-dialog');
const removeKeyForm = document.querySelector('#remove-key-form');
const removeKeyName = document.querySelector('#remove-key-name');
const removeKeyError = document.querySelector('#remove-key-error');
const removeKeySubmit = document.querySelector('#remove-key-submit');
const accountMenu = document.querySelector('#account-menu');
const avatarButton = document.querySelector('#avatar-button');
const avatarInitial = document.querySelector('#avatar-initial');
const accountPopper = document.querySelector('#account-popper');
const navCurrentUser = document.querySelector('#nav-current-user');
const logoutButton = document.querySelector('#logout-button');
let mode = 'login';
let editingKeyId = null;
let removingKeyId = null;

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

function formatNumber(value) {
  return new Intl.NumberFormat('zh-TW').format(value);
}

function setAccountPopper(open, restoreFocus = false) {
  avatarButton.setAttribute('aria-expanded', String(open));
  accountPopper.classList.toggle('hidden', !open);
  if (restoreFocus) avatarButton.focus();
}

function getAvatarInitial(username) {
  return username.match(/[a-z0-9]/i)?.[0].toUpperCase() ?? username[0];
}

function openKeyNameDialog(key = null) {
  editingKeyId = key?.id ?? null;
  document.querySelector('#key-name-title').textContent = key ? '編輯 Key 名稱' : '建立 API Key';
  keyNameSubmit.textContent = key ? '儲存' : '建立';
  keyNameInput.value = key?.name ?? '';
  keyNameError.textContent = '';
  keyNameDialog.showModal();
  keyNameInput.focus();
}

function createIcon(name) {
  const icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  icon.classList.add('icon');
  icon.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
  use.setAttribute('href', `#icon-${name}`);
  icon.append(use);
  return icon;
}

function openRemoveKeyDialog(key) {
  removingKeyId = key.id;
  removeKeyName.textContent = key.name;
  removeKeyError.textContent = '';
  removeKeyDialog.showModal();
}

function renderKeys(keys) {
  keyList.replaceChildren();
  if (!keys.length) {
    const row = document.createElement('tr');
    const empty = document.createElement('td');
    empty.className = 'empty';
    empty.colSpan = 6;
    empty.textContent = '尚未建立任何 API Key。';
    row.append(empty);
    keyList.append(row);
    return;
  }
  for (const key of keys) {
    const row = document.createElement('tr');
    const nameCell = document.createElement('td');
    nameCell.className = 'key-name';
    nameCell.dataset.label = '名稱';
    const name = document.createElement('strong');
    name.textContent = key.name;
    nameCell.append(name);
    const valueCell = document.createElement('td');
    valueCell.dataset.label = 'API Key';
    const value = document.createElement('code');
    value.textContent = key.display;
    valueCell.append(value);
    const created = document.createElement('td');
    created.className = 'key-date';
    created.dataset.label = '建立時間';
    created.textContent = formatDate(key.created_at);
    const used = document.createElement('td');
    used.className = 'key-date';
    used.dataset.label = '最近使用';
    used.textContent = formatDate(key.last_used_at);
    const usageCell = document.createElement('td');
    usageCell.dataset.label = '用量';
    const usage = document.createElement('div');
    usage.className = 'key-usage';
    const tokens = document.createElement('strong');
    tokens.textContent = `${formatNumber(key.usage.total_tokens)} Tokens`;
    const requests = document.createElement('span');
    requests.textContent = `${formatNumber(key.usage.requests)} 次請求`;
    usage.append(tokens, requests);
    usageCell.append(usage);
    const editButton = document.createElement('button');
    editButton.className = 'icon-button';
    editButton.type = 'button';
    editButton.setAttribute('aria-label', `編輯 ${key.name}`);
    editButton.dataset.tooltip = '編輯名稱';
    editButton.append(createIcon('pencil'));
    editButton.addEventListener('click', () => openKeyNameDialog(key));
    const removeButton = document.createElement('button');
    removeButton.className = 'icon-button icon-button-danger';
    removeButton.type = 'button';
    removeButton.setAttribute('aria-label', `移除 ${key.name}`);
    removeButton.dataset.tooltip = '移除 Key';
    removeButton.append(createIcon('trash'));
    removeButton.addEventListener('click', () => openRemoveKeyDialog(key));
    const actionsCell = document.createElement('td');
    actionsCell.dataset.label = '操作';
    const actions = document.createElement('div');
    actions.className = 'key-actions';
    actions.append(editButton, removeButton);
    actionsCell.append(actions);
    row.append(nameCell, valueCell, created, used, usageCell, actionsCell);
    keyList.append(row);
  }
}

async function loadAccount() {
  try {
    const body = await request('/api/me');
    const username = body.message.username;
    document.querySelector('#current-user').textContent = username;
    navCurrentUser.textContent = username;
    avatarInitial.textContent = getAvatarInitial(username);
    avatarButton.setAttribute('aria-label', `開啟 ${username} 的帳號選單`);
    accountMenu.classList.remove('hidden');
    renderKeys(body.message.keys);
    authView.classList.add('hidden');
    dashboardView.classList.remove('hidden');
  } catch {
    setAccountPopper(false);
    accountMenu.classList.add('hidden');
    dashboardView.classList.add('hidden');
    authView.classList.remove('hidden');
  }
}

loginTab.addEventListener('click', () => setMode('login'));
registerTab.addEventListener('click', () => setMode('register'));

avatarButton.addEventListener('click', () => {
  setAccountPopper(accountPopper.classList.contains('hidden'));
});

accountMenu.addEventListener('focusout', (event) => {
  if (!accountMenu.contains(event.relatedTarget)) setAccountPopper(false);
});

document.addEventListener('click', (event) => {
  if (!accountMenu.contains(event.target)) setAccountPopper(false);
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !accountPopper.classList.contains('hidden')) {
    setAccountPopper(false, true);
  }
});

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

document.querySelector('#create-key-button').addEventListener('click', () => {
  openKeyNameDialog();
});

document.querySelector('#key-name-cancel').addEventListener('click', () => {
  keyNameDialog.close();
});

document.querySelector('#remove-key-cancel').addEventListener('click', () => {
  removeKeyDialog.close();
});

removeKeyDialog.addEventListener('close', () => {
  removingKeyId = null;
  removeKeyError.textContent = '';
});

removeKeyForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const keyId = removingKeyId;
  if (!keyId) return;

  removeKeyError.textContent = '';
  removeKeySubmit.disabled = true;
  try {
    await request(`/api/keys/${keyId}`, { method: 'DELETE' });
    removeKeyDialog.close();
    showToast('API Key 已移除');
    await loadAccount();
  } catch (error) {
    removeKeyError.textContent = error.message;
  } finally {
    removeKeySubmit.disabled = false;
  }
});

keyNameForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  keyNameError.textContent = '';
  keyNameSubmit.disabled = true;
  const name = keyNameInput.value;
  try {
    if (editingKeyId) {
      await request(`/api/keys/${editingKeyId}`, {
        method: 'PATCH',
        body: JSON.stringify({ name }),
      });
      showToast('Key 名稱已更新');
    } else {
      const body = await request('/api/keys', {
        method: 'POST',
        body: JSON.stringify({ name }),
      });
      newKeyValue.textContent = body.message.api_key;
      newKeyStatus.textContent = '';
    }
    keyNameDialog.close();
    if (!editingKeyId) newKeyDialog.showModal();
    await loadAccount();
  } catch (error) {
    keyNameError.textContent = error.message;
  } finally {
    keyNameSubmit.disabled = false;
  }
});

document.querySelector('#copy-key-button').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(newKeyValue.textContent);
    newKeyStatus.textContent = 'API Key 已複製';
  } catch {
    newKeyStatus.textContent = '無法複製，請手動選取完整 Key。';
  }
});

document.querySelector('#new-key-close').addEventListener('click', () => {
  newKeyDialog.close();
});

newKeyDialog.addEventListener('close', () => {
  newKeyValue.textContent = '';
  newKeyStatus.textContent = '';
});

logoutButton.addEventListener('click', async () => {
  setAccountPopper(false);
  try {
    await request('/api/logout', { method: 'POST' });
  } finally {
    if (newKeyDialog.open) newKeyDialog.close();
    await loadAccount();
  }
});

loadAccount();
