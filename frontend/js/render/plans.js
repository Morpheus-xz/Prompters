/** Data-in, DOM-out plan creation and navigation views. */
import {h, field, select, date} from '../dom.js';

/** Render the owner-scoped sidebar. */
export function planList(plans, current, onOpen) {
  if (!plans.length) return h('p', {className: 'muted'}, 'Your next good memory starts here.');
  return h('ul', {className: 'plan-list'}, plans.map(plan => h('li', {},
    h('button', {type: 'button', className: plan.id === current ? 'selected' : '',
      'aria-current': plan.id === current ? 'true' : null, onClick: () => onOpen(plan.id)},
    h('strong', {}, plan.title), h('small', {}, date(plan.event_date))))));
}
/** Render the event brief; registry data drives the split preview. */
export function createForm(types, onSubmit) {
  const type = select(types.map(item => [item.key, item.label]), types[0].key, {required: true});
  const preview = h('ul', {className: 'preview'});
  const update = () => preview.replaceChildren(...types.find(item => item.key === type.value)
    .budget_split.map(line => h('li', {}, h('span', {}, line.label), h('strong', {}, `${line.percent}%`))));
  type.addEventListener('change', update);
  update();
  const form = h('form', {id: 'create-form', onSubmit},
    h('div', {className: 'form-grid'},
      field('title', 'What are we celebrating?', h('input', {required: true, maxlength: 80, placeholder: 'e.g. Maya & Arjun’s wedding'}), 'Give your celebration a name.'),
      field('event_type', 'Event type', type, 'A practical starting point, tailored to your event.'),
      field('event_date', 'Event date', h('input', {type: 'date', required: true}), 'Choose a future date within five years.'),
      field('guest_count', 'Number of guests', h('input', {type: 'number', min: 1, max: 5000, required: true, value: 50}), 'Include everyone you expect to host.'),
      field('total_budget', 'Total budget', h('input', {type: 'number', min: 0.01, max: 1000000000, step: '0.01', required: true, placeholder: '100000'}), 'We’ll allocate every last cent.'),
      field('currency', 'Currency', select(['INR', 'USD', 'EUR', 'GBP'].map(v => [v, v]), 'INR'), 'One currency throughout your plan.'),
      field('city', 'City (optional)', h('input', {maxlength: 60, placeholder: 'Where people come together'})),
      field('preferences', 'Make it yours (optional)', h('textarea', {maxlength: 300, rows: 3, placeholder: 'A garden setting, vegetarian food, a love of live music…'}), 'Interests, traditions, dietary needs or accessibility preferences.')),
    h('div', {className: 'split-box'}, h('h3', {}, 'A starting point for your budget'), preview),
    h('button', {type: 'submit', className: 'primary'}, 'Create my plan →'));
  return h('div', {className: 'create-view'}, h('p', {className: 'eyebrow'}, 'LESS OVERWHELM. MORE OCCASION.'),
    h('h1', {}, 'Something worth', h('br'), h('em', {}, 'coming together for.')),
    h('p', {className: 'intro'}, 'Turn your big idea into a clear budget, a doable timeline and the little details that make it yours.'),
    h('div', {className: 'form-card'}, h('h2', {}, 'Let’s set the scene'), form));
}
/** Render the dashboard header and in-page navigation. */
export function planHeader(plan, onDelete) {
  return h('div', {}, h('p', {className: 'eyebrow'}, `${plan.event_type} · ${date(plan.event_date)} · ${plan.guest_count} guests`),
    h('div', {className: 'title-row'}, h('h1', {id: 'plan-heading', tabindex: '-1'}, plan.title),
      h('button', {type: 'button', className: 'quiet', onClick: onDelete}, 'Delete plan')),
    h('div', {className: 'readiness'}, h('strong', {}, `${plan.progress.days_until_event} days to go`),
      h('label', {for: 'readiness'}, `${plan.progress.readiness_score}% ready to celebrate`),
      h('progress', {id: 'readiness', max: 100, value: plan.progress.readiness_score}, `${plan.progress.readiness_score}%`)),
    h('nav', {'aria-label': 'Plan sections', className: 'section-nav'},
      ['Budget', 'Timeline', 'Vendor checklist', 'Ideas for you'].map((label, index) =>
        h('a', {href: `#${['budget', 'timeline', 'vendors', 'ideas'][index]}`}, label))));
}
