import assert from 'node:assert/strict';
import { beforeEach, test } from 'node:test';
import { h, field } from '../js/dom.js';
import { createForm } from '../js/render/create-plan.js';
import { budgetView } from '../js/render/budget.js';
import { timelineView } from '../js/render/timeline.js';
import { vendorsView } from '../js/render/vendors.js';
import { ideasView } from '../js/render/ideas.js';
import { planHeader, planList } from '../js/render/plans.js';
import { installDom, eventTypes, planFixture } from './helpers.js';

beforeEach(() => installDom());

test('DOM builder treats untrusted strings as literal text and flattens children', () => {
  const node = h(
    'div',
    { className: 'safe' },
    ['<script>unsafe()</script>', [0, null, false]],
    h('span', {}, 'ok'),
  );
  assert.equal(node.querySelector('script'), null);
  assert.equal(node.textContent, '<script>unsafe()</script>0ok');
  assert.equal(node.className, 'safe');
  assert.equal(h('p', { textContent: 'literal' }).textContent, 'literal');
});

test('form preview follows the registry and submitting preserves native form semantics', () => {
  let submitted;
  const view = createForm(eventTypes(), (form) => {
    submitted = form;
  });
  document.body.append(view);
  const control = view.querySelector('#event_type');
  assert.match(view.querySelector('.preview').textContent, /25%/);
  control.value = 'birthday';
  control.dispatchEvent(new Event('change'));
  assert.match(view.querySelector('.preview').textContent, /20%/);
  const form = view.querySelector('form');
  const event = new Event('submit', { cancelable: true });
  form.dispatchEvent(event);
  assert.equal(event.defaultPrevented, true);
  assert.equal(submitted, form);
  assert.equal(view.querySelectorAll('h1').length, 1);
});

test('field errors are local, associated with controls, and clear when edited', () => {
  const input = h('input', { required: true });
  const view = field('name', 'Name', input, 'A hint');
  document.body.append(view);
  input.dispatchEvent(new Event('invalid'));
  assert.equal(input.getAttribute('aria-invalid'), 'true');
  assert.ok(view.querySelector('.error').textContent);
  input.value = 'Now valid';
  input.dispatchEvent(new Event('input'));
  assert.equal(input.hasAttribute('aria-invalid'), false);
  assert.equal(view.querySelector('.error').textContent, '');
  assert.equal(input.getAttribute('aria-describedby'), 'name-hint name-error');
});

test('budget renders server values, explicit overspend text and expense callbacks', () => {
  const removed = [];
  const plan = planFixture();
  const view = budgetView(
    plan,
    () => {},
    (id) => removed.push(id),
  );
  assert.equal(view.id, 'budget');
  assert.equal(view.querySelectorAll('tbody tr').length, 2);
  assert.match(view.textContent, /Over budget/);
  assert.equal(view.querySelector('meter').value, 100);
  view.querySelector('.expense-list button').click();
  assert.deepEqual(removed, ['expense-1']);
  assert.equal(view.querySelector('#category').options.length, 2);
});

test('timeline receives its date explicitly and sends native completion changes', () => {
  const changed = [];
  const view = timelineView(
    planFixture(),
    (id, done) => changed.push([id, done]),
    '2026-01-02',
  );
  assert.match(view.textContent, /Overdue/);
  assert.match(view.textContent, /compressed the schedule/);
  const checkbox = view.querySelector('input');
  checkbox.checked = true;
  checkbox.dispatchEvent(new Event('change'));
  assert.deepEqual(changed, [['task-01', true]]);
  const later = timelineView(planFixture(), () => {}, '2025-01-01');
  assert.doesNotMatch(later.textContent, /Overdue/);
});

test('vendor selections retain accessible labels and essential badges', () => {
  const changed = [];
  const view = vendorsView(planFixture(), (id, status) => changed.push([id, status]));
  const control = view.querySelector('select');
  assert.equal(view.querySelector('label').htmlFor, control.id);
  assert.match(view.textContent, /Essential/);
  control.value = 'booked';
  control.dispatchEvent(new Event('change'));
  assert.deepEqual(changed, [['vendor-01', 'booked']]);
});

test('ideas group by category and distinguish generate from refresh', () => {
  const calls = [];
  const response = {
    ideas: [
      {
        title: '<img src=x>',
        description: 'Seasonal food',
        budget_category: 'catering',
        cost_level: 'low',
      },
    ],
    pro_tip: 'Confirm with vendors',
    focus: 'food',
    from_cache: true,
  };
  const view = ideasView(planFixture(), response, (...args) => calls.push(args));
  assert.equal(view.querySelector('img'), null);
  assert.match(view.querySelector('.idea-group h4').textContent, /Food/);
  assert.match(view.textContent, /Saved ideas/);
  for (const button of view.querySelectorAll('button')) button.click();
  assert.deepEqual(calls, [
    ['food', false],
    ['food', true],
  ]);
  assert.equal(view.querySelectorAll('article').length, 1);
});

test('empty views and plan navigation retain their descriptive content', () => {
  assert.match(
    ideasView(planFixture(), null, () => {}).textContent,
    /add a little personality/,
  );
  assert.match(planList([], undefined, () => {}).textContent, /starts here/);
  const opened = [];
  const sidebar = planList([planFixture()], 'plan-1', (id) => opened.push(id));
  sidebar.querySelector('button').click();
  assert.deepEqual(opened, ['plan-1']);
  assert.equal(sidebar.querySelector('button').getAttribute('aria-current'), 'true');
  const header = planHeader(planFixture(), () => {});
  assert.equal(header.querySelector('progress').value, 0);
  assert.equal(header.querySelectorAll('nav a').length, 4);
});
