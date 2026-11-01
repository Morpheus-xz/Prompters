/** The application's only network boundary. */
export async function api(path, method = 'GET', body) {
  let response;
  try {
    response = await fetch(path, {method, credentials: 'same-origin',
      headers: body ? {'Content-Type': 'application/json'} : {},
      body: body ? JSON.stringify(body) : undefined});
  } catch {
    throw new Error('Connection lost. Check your connection and try again.');
  }
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) {
    const message = Array.isArray(data.detail)
      ? data.detail.map(item => `${item.loc.at(-1)}: ${item.msg}`).join('; ')
      : data.detail || 'Something went wrong. Please try again.';
    const error = new Error(response.status === 429 ? 'Too many requests. Please wait a minute.' : message);
    error.fields = Array.isArray(data.detail) ? data.detail : [];
    throw error;
  }
  return data;
}
