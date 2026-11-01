/** Safe DOM primitives; user strings are always text nodes. */
export function h(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key.startsWith('on')) node.addEventListener(key.slice(2).toLowerCase(), value);
    else if (key === 'className') node.className = value;
    else if (key === 'textContent') node.textContent = value;
    else if (value !== false && value != null) node.setAttribute(key, String(value));
  }
  for (const child of children.flat(Infinity)) {
    if (child != null) node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}
/** Format server-computed money in the plan currency. */
export function money(value, currency) {
  return new Intl.NumberFormat(undefined, {style: 'currency', currency}).format(value);
}
/** Interpret date-only values in local time without a timezone shift. */
export function date(value) {
  return new Intl.DateTimeFormat(undefined, {dateStyle: 'medium'}).format(new Date(`${value}T12:00:00`));
}
/** Render a labeled control with hint and inline error targets. */
export function field(name, label, control, hint = '') {
  control.id = name;
  control.name = name;
  control.setAttribute('aria-describedby', `${name}-hint ${name}-error`);
  control.addEventListener('invalid', () => {
    control.setAttribute('aria-invalid', 'true');
    document.getElementById(`${name}-error`).textContent = control.validationMessage;
  });
  control.addEventListener('input', () => {
    control.removeAttribute('aria-invalid');
    document.getElementById(`${name}-error`).textContent = '';
  });
  return h('div', {className: 'field'}, h('label', {for: name}, label), control,
    h('small', {id: `${name}-hint`}, hint), h('span', {id: `${name}-error`, className: 'error'}));
}
/** Populate a select using ordinary text content. */
export function select(options, value, props = {}) {
  const node = h('select', props, options.map(([key, label]) => h('option', {value: key}, label)));
  node.value = value;
  return node;
}
/** Label the four deliverables consistently. */
export function section(id, number, title, subtitle, ...content) {
  return h('section', {id, 'aria-labelledby': `${id}-title`},
    h('div', {className: 'section-heading'}, h('span', {className: 'section-number'}, number),
      h('div', {}, h('h3', {id: `${id}-title`}, title), h('p', {}, subtitle))), ...content);
}
