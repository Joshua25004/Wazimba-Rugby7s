const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

export async function api(path, options = {}) {
  const token = localStorage.getItem('wazimbaToken');
  const headers = { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: `Token ${token}` } : {}), ...options.headers };
  const response = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    const fieldError = Object.entries(detail).find(([key]) => !['detail', 'non_field_errors'].includes(key));
    const message = detail.detail || detail.non_field_errors?.[0] || (fieldError ? `${fieldError[0]}: ${Array.isArray(fieldError[1]) ? fieldError[1].join(' ') : fieldError[1]}` : `Request failed (${response.status})`);
    throw new Error(message);
  }
  if (response.status === 204) return null;
  if (response.headers.get('content-type')?.includes('text/csv')) return response.text();
  return response.json();
}

export async function getAll(path) {
  let url = path;
  const rows = [];
  do {
    const result = await api(url);
    if (Array.isArray(result)) return result;
    rows.push(...(result.results || []));
    if (!result.next) break;
    const parsed = new URL(result.next);
    url = `${parsed.pathname.replace('/api', '')}${parsed.search}`;
  } while (url);
  return rows;
}

export async function download(path, filename) {
  const token = localStorage.getItem('wazimbaToken');
  const response = await fetch(`${BASE}${path}`, { headers: token ? { Authorization: `Token ${token}` } : {} });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url; anchor.download = filename; anchor.click();
  URL.revokeObjectURL(url);
}
