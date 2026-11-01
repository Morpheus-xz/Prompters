/** Accessible request feedback, serialization and form-error presentation. */
/** @import {AppState} from "../types/contracts.js" */
import { ApiError } from './api.js';
import { state } from './state.js';

/** @param {string} message */
export function announce(message) {
  const region = document.getElementById('status');
  if (region) region.textContent = message;
}

/**
 * @param {boolean} loading
 * @param {AppState} store
 */
function setLoading(loading, store) {
  store.busy = loading;
  document.getElementById('workspace')?.setAttribute('aria-busy', String(loading));
  const controls = document.querySelectorAll('button, input, select, textarea');
  for (const control of controls) {
    if (
      control instanceof HTMLButtonElement ||
      control instanceof HTMLInputElement ||
      control instanceof HTMLSelectElement ||
      control instanceof HTMLTextAreaElement
    ) {
      control.disabled = loading;
    }
  }
}

/** @param {unknown} error */
function showError(error) {
  announce(
    error instanceof Error ? error.message : 'Something went wrong. Please try again.',
  );
  if (!(error instanceof ApiError)) return;
  for (const { field, message } of error.fields) {
    document.getElementById(field)?.setAttribute('aria-invalid', 'true');
    const target = document.getElementById(`${field}-error`);
    if (target) target.textContent = message;
  }
}

/**
 * @param {() => Promise<void>} action
 * @param {string} message
 * @param {() => void} render
 * @param {AppState} [store]
 */
export async function runAction(action, message, render, store = state) {
  if (store.busy) return false;
  const focusId = document.activeElement?.id;
  setLoading(true, store);
  announce('Working on it…');
  try {
    await action();
    render();
    announce(message);
    return true;
  } catch (error) {
    showError(error);
    return false;
  } finally {
    setLoading(false, store);
    if (focusId) document.getElementById(focusId)?.focus();
  }
}
