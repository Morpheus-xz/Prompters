/** Form extraction and shared monetary controls; server validation remains authoritative. */
/** @import {CreatePlanInput, Currency, EventType, ExpenseInput} from "../types/contracts.js" */
import { field, h } from './dom.js';
import { FORM_LIMITS } from './config.js';

/**
 * @param {string} name
 * @param {string} label
 * @param {string} [hint]
 * @param {string} [placeholder]
 */
export function moneyField(name, label, hint = '', placeholder = '') {
  const input = h('input', {
    type: 'number',
    min: FORM_LIMITS.moneyStep,
    max: FORM_LIMITS.budget,
    step: FORM_LIMITS.moneyStep,
    required: true,
    placeholder,
  });
  return field(name, label, input, hint);
}

/**
 * @param {FormData} data
 * @param {string} name
 */
function textValue(data, name) {
  return String(data.get(name) ?? '').trim();
}

/** @param {HTMLFormElement} form @returns {CreatePlanInput} */
export function planInput(form) {
  const data = new FormData(form);
  return {
    title: textValue(data, 'title'),
    event_type: /** @type {EventType} */ (textValue(data, 'event_type')),
    event_date: textValue(data, 'event_date'),
    guest_count: Number(textValue(data, 'guest_count')),
    total_budget: Number(textValue(data, 'total_budget')),
    currency: /** @type {Currency} */ (textValue(data, 'currency')),
    city: textValue(data, 'city') || null,
    preferences: textValue(data, 'preferences') || null,
  };
}

/** @param {HTMLFormElement} form @returns {ExpenseInput} */
export function expenseInput(form) {
  const data = new FormData(form);
  return {
    category: textValue(data, 'category'),
    amount: Number(textValue(data, 'amount')),
    description: textValue(data, 'description'),
  };
}

/**
 * @param {HTMLFormElement} form
 * @param {(form: HTMLFormElement) => void} onSubmit
 */
export function submitHandler(form, onSubmit) {
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    onSubmit(form);
  });
}
