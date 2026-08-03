const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const TOKEN_KEY = 'auth_token';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function extractErrorMessage(data, status) {
  if (!data) return `Request failed with status ${status}`;
  if (typeof data === 'string') return data;
  if (data.error) return data.error;
  if (data.detail) return data.detail;
  // DRF's default serializer validation error shape: { field_name: ["msg1", "msg2"], ... }
  const fieldErrors = Object.entries(data)
    .filter(([, value]) => Array.isArray(value))
    .map(([field, messages]) => `${field}: ${messages.join(' ')}`);
  if (fieldErrors.length > 0) return fieldErrors.join(' ');
  return `Request failed with status ${status}`;
}

async function request(path, options = {}) {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    // An expired/invalid token is never recoverable by retrying — clear it so the app falls
    // back to the logged-out state instead of repeatedly sending a dead token.
    if (res.status === 401) clearToken();
    throw new Error(extractErrorMessage(data, res.status));
  }

  return data;
}

export const api = {
  register: (email, password) =>
    request('/auth/register/', { method: 'POST', body: JSON.stringify({ email, password }) }),
  login: (email, password) =>
    request('/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me: () => request('/auth/me/'),
  forgotPassword: (email) =>
    request('/auth/forgot-password/', { method: 'POST', body: JSON.stringify({ email }) }),
  verifyOtp: ({ email, otp }) =>
    request('/auth/verify-otp/', { method: 'POST', body: JSON.stringify({ email, otp }) }),
  resetPassword: ({ email, otp, password }) =>
    request('/auth/reset-password/', { method: 'POST', body: JSON.stringify({ email, otp, password }) }),

  listRepos: () => request('/repos/'),
  getRepo: (id) => request(`/repos/${id}/`),
  createRepo: (githubUrl) =>
    request('/repos/', {
      method: 'POST',
      body: JSON.stringify({ github_url: githubUrl }),
    }),
  deleteRepo: (id) => request(`/repos/${id}/`, { method: 'DELETE' }),
  updateRepo: (id, { displayName, description }) =>
    request(`/repos/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ display_name: displayName, description }),
    }),
  getFileContent: (repoId, path) =>
    request(`/repos/${repoId}/file/?path=${encodeURIComponent(path)}`),
  getStaleness: (repoId) => request(`/repos/${repoId}/staleness/`),
  reindexRepo: (repoId) => request(`/repos/${repoId}/reindex/`, { method: 'POST' }),

  sendChatMessage: (repoId, message, sessionId) =>
    request(`/repos/${repoId}/chat/`, {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId }),
    }),
  getChatHistory: (repoId, sessionId) =>
    request(`/repos/${repoId}/chat/history/?session_id=${sessionId}`),
  listChatSessions: (repoId) => request(`/repos/${repoId}/chat/sessions/`),
  deleteChatSession: (repoId, sessionId) =>
    request(`/repos/${repoId}/chat/sessions/${encodeURIComponent(sessionId)}/`, { method: 'DELETE' }),

  getRecommendations: (repoId, refresh = false) =>
    request(`/repos/${repoId}/recommendations/${refresh ? '?refresh=true' : ''}`),
  getArchitecture: (repoId, refresh = false) =>
    request(`/repos/${repoId}/architecture/${refresh ? '?refresh=true' : ''}`),

  listPrDrafts: (repoId) => request(`/repos/${repoId}/pr-draft/`),
  createPrDraft: (repoId, { issueNumber, taskDescription }) =>
    request(`/repos/${repoId}/pr-draft/`, {
      method: 'POST',
      body: JSON.stringify({ issue_number: issueNumber ?? null, task_description: taskDescription || '' }),
    }),

  listTestDrafts: (repoId) => request(`/repos/${repoId}/tests/`),
  createTestDraft: (repoId, { targetFile, taskDescription }) =>
    request(`/repos/${repoId}/tests/`, {
      method: 'POST',
      body: JSON.stringify({ target_file: targetFile || '', task_description: taskDescription || '' }),
    }),
};
