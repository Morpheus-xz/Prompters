/** Safe DOM construction: property wiring and literal text have one boundary. */
/** @import {Choice, DomChild, DomProps, FormControl} from "../types/contracts.js" */

/**
 * @template {keyof HTMLElementTagNameMap} Tag
 * @param {Tag} tag
 * @param {DomProps} [props]
 * @param {...DomChild} children
 * @returns {HTMLElementTagNameMap[Tag]}
 */
export function h(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(props)) applyProperty(node, name, value);
  for (const child of children) appendChild(node, child);
  return node;
}

/**
 * @param {HTMLElement} node
 * @param {DomChild} child
 */
function appendChild(node, child) {
  if (Array.isArray(child)) {
    for (const nested of child) appendChild(node, nested);
  } else if (child !== null && child !== undefined && child !== false) {
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
}

/**
 * @param {HTMLElement} node
 * @param {string} name
 * @param {DomProps[string]} value
 */
function applyProperty(node, name, value) {
  if (value === false || value === null || value === undefined) return;
  if (typeof value === 'function') {
    if (name.startsWith('on')) {
      node.addEventListener(name.slice(2).toLowerCase(), value);
    }
    return;
  }
  if (name === 'className') node.className = String(value);
  else if (name === 'textContent') node.textContent = String(value);
  else node.setAttribute(name, String(value));
}

/**
 * @param {number} value
 * @param {string} currency
 */
export function money(value, currency) {
  return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(
    value,
  );
}

/**
 * Format a date-only server value without shifting its calendar date.
 * @param {string} value
 */
export function date(value) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(
    new Date(`${value}T12:00:00`),
  );
}

/**
 * @param {string} name
 * @param {string} label
 * @param {FormControl} control
 * @param {string} [hint]
 */
export function field(name, label, control, hint = '') {
  const error = h('span', { id: `${name}-error`, className: 'error' });
  control.id = name;
  control.name = name;
  control.setAttribute('aria-describedby', `${name}-hint ${name}-error`);
  control.addEventListener('invalid', () => {
    control.setAttribute('aria-invalid', 'true');
    error.textContent = control.validationMessage;
  });
  control.addEventListener('input', () => {
    control.removeAttribute('aria-invalid');
    error.textContent = '';
  });
  return h(
    'div',
    { className: 'field' },
    h('label', { for: name }, label),
    control,
    h('small', { id: `${name}-hint` }, hint),
    error,
  );
}

/**
 * @param {readonly Choice[]} options
 * @param {string} value
 * @param {DomProps} [props]
 */
export function select(options, value, props = {}) {
  const control = h(
    'select',
    props,
    options.map(([key, label]) => h('option', { value: key }, label)),
  );
  control.value = value;
  return control;
}

/**
 * @param {string} id
 * @param {string} number
 * @param {string} title
 * @param {string} subtitle
 * @param {...DomChild} content
 */
export function section(id, number, title, subtitle, ...content) {
  const heading = h(
    'div',
    { className: 'section-heading' },
    h('span', { className: 'section-number' }, number),
    h('div', {}, h('h3', { id: `${id}-title` }, title), h('p', {}, subtitle)),
  );
  return h('section', { id, 'aria-labelledby': `${id}-title` }, heading, ...content);
}
