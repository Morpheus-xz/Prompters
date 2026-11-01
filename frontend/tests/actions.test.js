import assert from 'node:assert/strict';
import test from 'node:test';
import { PlanActions } from '../js/actions.js';
import { discardPlan, rememberPlan, selectPlan } from '../js/state.js';
import { emptyState, planFixture, eventTypes } from './helpers.js';

/** Record injected requests and respond with detached public API state. */
function actionFixture(response = planFixture()) {
  const calls = [];
  const store = emptyState();
  const request = async (...args) => {
    calls.push(args);
    return structuredClone(response);
  };
  return { actions: new PlanActions(request, store), store, calls };
}

test('selection transitions invalidate ideas and sidebar entries coherently', () => {
  const store = emptyState();
  const plan = planFixture();
  rememberPlan(plan, store);
  assert.equal(store.plan, plan);
  assert.equal(store.plans[0].id, plan.id);
  store.ideas = { ideas: [] };
  selectPlan(plan, store);
  assert.equal(store.ideas, null);
  discardPlan(plan.id, store);
  assert.deepEqual(store.plans, []);
  assert.equal(store.plan, null);
});

test('create uses its authoritative response without a second list request', async () => {
  const { actions, store, calls } = actionFixture();
  await actions.createPlan({ title: 'Party' });
  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0], ['/plans', 'POST', { title: 'Party' }]);
  assert.equal(store.plan.id, 'plan-1');
  assert.equal(store.plans[0].id, store.plan.id);
});

test('opening another plan clears the previous creative results', async () => {
  const { actions, store, calls } = actionFixture();
  store.ideas = { ideas: [] };
  await actions.openPlan('plan-1');
  assert.deepEqual(calls[0], ['/plans/plan-1']);
  assert.equal(store.ideas, null);
});

test('mutation methods use the selected plan and preserve unrelated ideas', async () => {
  const { actions, store, calls } = actionFixture();
  store.plan = planFixture();
  const ideas = { ideas: [] };
  store.ideas = ideas;
  await actions.addExpense({ category: 'venue', amount: 1, description: 'Deposit' });
  await actions.removeExpense('expense-1');
  await actions.updateTask('task-01', true);
  await actions.updateVendor('vendor-01', 'booked');
  assert.deepEqual(
    calls.map((call) => call.slice(0, 2)),
    [
      ['/plans/plan-1/expenses', 'POST'],
      ['/plans/plan-1/expenses/expense-1', 'DELETE'],
      ['/plans/plan-1/tasks/task-01', 'PATCH'],
      ['/plans/plan-1/vendors/vendor-01', 'PATCH'],
    ],
  );
  assert.equal(store.ideas, ideas);
});

test('failed deletion leaves selected plan and sidebar intact', async () => {
  const store = emptyState();
  rememberPlan(planFixture(), store);
  const actions = new PlanActions(async () => {
    throw new Error('Unavailable');
  }, store);
  await assert.rejects(actions.deletePlan(), /Unavailable/);
  assert.equal(store.plan.id, 'plan-1');
  assert.equal(store.plans.length, 1);
});

test('accepted deletion removes the selected plan and its ideas', async () => {
  const { actions, store, calls } = actionFixture(null);
  rememberPlan(planFixture(), store);
  store.ideas = { ideas: [] };
  await actions.deletePlan();
  assert.deepEqual(calls[0], ['/plans/plan-1', 'DELETE']);
  assert.equal(store.plan, null);
  assert.equal(store.ideas, null);
  assert.deepEqual(store.plans, []);
});

test('ideas forward focus and refresh while keeping computed state untouched', async () => {
  const response = {
    ideas: [],
    focus: 'decor',
    pro_tip: 'Local flowers',
    from_cache: false,
  };
  const { actions, store, calls } = actionFixture(response);
  store.plan = planFixture();
  const before = structuredClone(store.plan);
  await actions.generateIdeas('decor', true);
  assert.deepEqual(calls[0], [
    '/plans/plan-1/ideas',
    'POST',
    { focus: 'decor', refresh: true },
  ]);
  assert.deepEqual(store.plan, before);
  assert.deepEqual(store.ideas, response);
});

test('updates without a selection are rejected before sending a request', async () => {
  const { actions, calls } = actionFixture();
  await assert.rejects(actions.updateTask('task-01', true), /Select a plan/);
  assert.equal(calls.length, 0);
});

test('initial data publishes only after both resources load successfully', async () => {
  const store = emptyState();
  const types = eventTypes();
  const actions = new PlanActions(async (path) => {
    if (path === '/event-types') return types;
    throw new Error('Unavailable');
  }, store);
  await assert.rejects(actions.loadInitialState(), /Unavailable/);
  assert.deepEqual(store.types, []);
  assert.deepEqual(store.plans, []);
});

test('bootstrap loads the owned sidebar and registry', async () => {
  const store = emptyState();
  const types = eventTypes();
  const plans = [planFixture()];
  const actions = new PlanActions(
    async (path) => (path === '/plans' ? plans : types),
    store,
  );
  await actions.loadInitialState();
  assert.equal(store.types, types);
  assert.equal(store.plans, plans);
});
