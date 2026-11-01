/** The single network boundary for browser requests and public API failures. */
/** @import {ErrorBody, FieldError} from "../types/contracts.js" */

/** Client-safe HTTP failure with optional normalized form validation errors. */
export class ApiError extends Error {
  /**
   * @param {string} message
   * @param {FieldError[]} [fields]
   */
  constructor(message, fields = []) {
    super(message);
    this.name = 'ApiError';
    this.fields = fields;
  }
}

/**
 * @param {number} status
 * @param {ErrorBody} body
 */
function responseError(status, body) {
  const fields = Array.isArray(body.detail)
    ? body.detail.map((issue) => ({
        field: String(issue.loc.at(-1)),
        message: issue.msg,
      }))
    : [];
  const detail =
    typeof body.detail === 'string'
      ? body.detail
      : fields.map((error) => `${error.field}: ${error.message}`).join('; ');
  const message =
    status === 429
      ? 'Too many requests. Please wait a minute.'
      : detail || 'Something went wrong. Please try again.';
  return new ApiError(message, fields);
}

/**
 * @template T
 * @param {string} path
 * @param {string} [method]
 * @param {object} [body]
 * @param {typeof fetch} [transport] Network dependency for offline verification.
 * @returns {Promise<T>}
 */
export async function api(path, method = 'GET', body, transport = fetch) {
  const response = await send(transport, path, method, body);
  if (response.status === 204) return /** @type {T} */ (/** @type {unknown} */ (null));
  let data;
  try {
    data = await response.json();
  } catch {
    throw new ApiError('The server returned an unexpected response. Please try again.');
  }
  if (!response.ok) throw responseError(response.status, data ?? {});
  return data;
}

/**
 * @param {typeof fetch} transport
 * @param {string} path
 * @param {string} method
 * @param {object} [body]
 */
async function send(transport, path, method, body) {
  try {
    return await transport(path, {
      method,
      credentials: 'same-origin',
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError('Connection lost. Check your connection and try again.');
  }
}
