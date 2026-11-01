import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { setImmediate as nextTurn } from 'node:timers/promises';
import test from 'node:test';
import { PlanActions } from '../js/actions.js';
import { PlannerApp } from '../js/application.js';
import { emptyState, eventTypes, installDom, planFixture } from './helpers.js';

/** Exercise the real application controller using an injected API implementation. */
function applicationFixture(initialPlan = null) {
  const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
  installDom(html);
  const calls = [];
  const store = emptyState();
  store.plan = initialPlan;
  const request = async (path, method = 'GET', body) => {
    calls.push({ path, method, body });
    if (path === '/event-types') return eventTypes();
    if (path === '/plans' && method === 'GET') return initialPlan ? [initialPlan] : [];
    return { ...planFixture(), title: body?.title || 'A joyful day' };
  };
  const app = new PlannerApp(new PlanActions(request, store));
  return { app, store, calls };
}

test('full create flow updates sidebar, dashboard, announcements and heading focus', async () => {
  const { app, store, calls } = applicationFixture();
  await app.start();
  document.getElementById('title').value = 'Garden wedding';
  document.getElementById('event_date').value = '2027-01-10';
  document.getElementById('total_budget').value = '10000';
  document
    .getElementById('create-form')
    .dispatchEvent(new Event('submit', { cancelable: true }));
  await nextTurn();
  assert.equal(store.plan.title, 'Garden wedding');
  assert.equal(document.getElementById('plan-heading').textContent, 'Garden wedding');
  assert.equal(document.activeElement.id, 'plan-heading');
  assert.equal(document.querySelectorAll('main section').length, 4);
  assert.match(document.getElementById('plans').textContent, /Garden wedding/);
  assert.equal(document.getElementById('status').textContent, 'Your plan is ready.');
  assert.equal(calls.filter((call) => call.method === 'POST').length, 1);
});

test('dashboard controls route native changes through the correct actions', async () => {
  const { app, calls } = applicationFixture(planFixture());
  await app.start();
  const checkbox = document.getElementById('task-01');
  checkbox.checked = true;
  checkbox.dispatchEvent(new Event('change'));
  await nextTurn();
  const vendor = document.getElementById('vendor-01');
  vendor.value = 'booked';
  vendor.dispatchEvent(new Event('change'));
  await nextTurn();
  assert.deepEqual(calls.slice(-2), [
    { path: '/plans/plan-1/tasks/task-01', method: 'PATCH', body: { done: true } },
    {
      path: '/plans/plan-1/vendors/vendor-01',
      method: 'PATCH',
      body: { status: 'booked' },
    },
  ]);
  assert.equal(document.getElementById('workspace').getAttribute('aria-busy'), 'false');
});

test('new-plan navigation clears selection and returns focus to the brief', async () => {
  const { app, store } = applicationFixture(planFixture());
  await app.start();
  document.getElementById('new-plan').click();
  assert.equal(store.plan, null);
  assert.equal(document.activeElement.id, 'title');
  assert.equal(store.plans.length, 1);
});

test('bootstrap failures render a useful retry path and announce the error', async () => {
  installDom(readFileSync(new URL('../index.html', import.meta.url), 'utf8'));
  const actions = new PlanActions(async () => {
    throw new Error('Connection lost');
  }, emptyState());
  await new PlannerApp(actions).start();
  assert.equal(document.querySelector('main h1').textContent, 'Let’s reconnect.');
  assert.match(document.getElementById('status').textContent, /Connection lost/);
  assert.equal(document.querySelector('main button').textContent, 'Try again');
});
