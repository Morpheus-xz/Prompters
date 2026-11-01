/** Event brief composition and registry-driven allocation preview. */
/** @import {EventTypeInfo} from "../../types/contracts.js" */
import { h, select } from '../dom.js';
import { submitHandler } from '../forms.js';
import {
  identityFields,
  scheduleFields,
  budgetFields,
  personalFields,
} from './plan-fields.js';

/**
 * @param {HTMLUListElement} preview
 * @param {EventTypeInfo[]} types
 * @param {string} key
 */
function updatePreview(preview, types, key) {
  const eventType = types.find((item) => item.key === key);
  if (!eventType) return;
  preview.replaceChildren(
    ...eventType.budget_split.map((line) =>
      h('li', {}, h('span', {}, line.label), h('strong', {}, `${line.percent}%`)),
    ),
  );
}

/**
 * @param {HTMLSelectElement} type
 * @param {HTMLUListElement} preview
 * @param {(form: HTMLFormElement) => void} onSubmit
 */
function eventForm(type, preview, onSubmit) {
  const fields = [
    identityFields(type),
    scheduleFields(),
    budgetFields(),
    personalFields(),
  ];
  const split = h(
    'div',
    { className: 'split-box' },
    h('h3', {}, 'A starting point for your budget'),
    preview,
  );
  const form = h(
    'form',
    { id: 'create-form' },
    h('div', { className: 'form-grid' }, fields),
    split,
    h('button', { type: 'submit', className: 'primary' }, 'Create my plan →'),
  );
  submitHandler(form, onSubmit);
  return form;
}

/** @param {HTMLFormElement} form */
function introduction(form) {
  return h(
    'div',
    { className: 'create-view' },
    h('p', { className: 'eyebrow' }, 'LESS OVERWHELM. MORE OCCASION.'),
    h('h1', {}, 'Something worth', h('br'), h('em', {}, 'coming together for.')),
    h(
      'p',
      { className: 'intro' },
      'Turn your big idea into a clear budget, a doable timeline and the little details that make it yours.',
    ),
    h('div', { className: 'form-card' }, h('h2', {}, 'Let’s set the scene'), form),
  );
}

/**
 * @param {EventTypeInfo[]} types
 * @param {(form: HTMLFormElement) => void} onSubmit
 */
export function createForm(types, onSubmit) {
  const type = select(
    types.map((item) => [item.key, item.label]),
    types[0].key,
    { required: true },
  );
  const preview = h('ul', { className: 'preview' });
  type.addEventListener('change', () => updatePreview(preview, types, type.value));
  updatePreview(preview, types, type.value);
  return introduction(eventForm(type, preview, onSubmit));
}
