/** Orchestration only: fetch state, render views and bind user actions. */
import {api} from './api.js';
import {h} from './dom.js';
import {state} from './state.js';
import {planList, createForm, planHeader} from './render/plans.js';
import {budgetView} from './render/budget.js';
import {timelineView} from './render/timeline.js';
import {vendorsView} from './render/vendors.js';
import {ideasView} from './render/ideas.js';

const workspace = document.querySelector('#workspace');
const dialog = document.querySelector('#delete-dialog');
/** Announce outcomes without interrupting keyboard focus. */
function announce(message) { document.querySelector('#status').textContent = message; }
/** Render sidebar and either the brief or the full dashboard. */
function render() {
  document.querySelector('#plans').replaceChildren(planList(state.plans, state.plan?.id, openPlan));
  if (!state.plan) { workspace.replaceChildren(createForm(state.types, createPlan)); return; }
  const plan = state.plan;
  workspace.replaceChildren(planHeader(plan, () => dialog.showModal()),
    h('h2', {className: 'sr-only'}, 'Your event plan'),
    budgetView(plan, addExpense, id => mutate(`/expenses/${id}`, 'DELETE')),
    timelineView(plan, (id, done) => mutate(`/tasks/${id}`, 'PATCH', {done})),
    vendorsView(plan, (id, status) => mutate(`/vendors/${id}`, 'PATCH', {status})),
    ideasView(plan, state.ideas, generateIdeas));
}
/** Serialize actions, expose loading state and map field errors inline. */
async function run(action, success) {
  if (state.busy) return;
  const focusId = document.activeElement?.id;
  state.busy = true;
  workspace.setAttribute('aria-busy', 'true');
  document.querySelectorAll('button, input, select, textarea').forEach(node => { node.disabled = true; });
  announce('Working on it…');
  try { await action(); render(); announce(success); }
  catch (error) {
    announce(error.message);
    for (const item of error.fields || []) {
      const name = item.loc.at(-1);
      document.getElementById(name)?.setAttribute('aria-invalid', 'true');
      const target = document.getElementById(`${name}-error`);
      if (target) target.textContent = item.msg;
    }
  } finally {
    state.busy = false;
    workspace.setAttribute('aria-busy', 'false');
    document.querySelectorAll('button, input, select, textarea').forEach(node => { node.disabled = false; });
    if (focusId) document.getElementById(focusId)?.focus();
  }
}
/** Load an existing celebration. */
async function openPlan(id) {
  await run(async () => { state.plan = await api(`/plans/${id}`); state.ideas = null; }, 'Plan opened.');
  document.querySelector('#plan-heading')?.focus();
}
/** Capture form data before disabling inputs. */
async function createPlan(event) {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  data.guest_count = Number(data.guest_count);
  data.total_budget = Number(data.total_budget);
  for (const key of ['city', 'preferences']) if (!data[key].trim()) data[key] = null;
  await run(async () => {
    state.plan = await api('/plans', 'POST', data);
    state.plans = await api('/plans');
    state.ideas = null;
  }, 'Your plan is ready.');
  document.querySelector('#plan-heading')?.focus();
}
/** Submit an expense in the plan currency. */
async function addExpense(event) {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  data.amount = Number(data.amount);
  await mutate('/expenses', 'POST', data);
}
/** Replace all dashboard data with the server's mutation response. */
async function mutate(path, method, body) {
  await run(async () => { state.plan = await api(`/plans/${state.plan.id}${path}`, method, body); }, 'Plan updated.');
}
/** Generate or refresh creative text without changing computed facts. */
async function generateIdeas(focus, refresh) {
  await run(async () => { state.ideas = await api(`/plans/${state.plan.id}/ideas`, 'POST', {focus, refresh}); }, 'Ideas ready.');
}
/** Delete only after the native dialog receives explicit confirmation. */
async function deletePlan() {
  dialog.close();
  await run(async () => {
    await api(`/plans/${state.plan.id}`, 'DELETE');
    state.plan = null; state.ideas = null; state.plans = await api('/plans');
  }, 'Plan deleted.');
  document.querySelector('#new-plan').focus();
}
/** Bootstrap same-origin metadata and owner identity. */
async function start() {
  try {
    state.types = await api('/event-types');
    state.plans = await api('/plans');
    render();
  } catch (error) {
    workspace.replaceChildren(h('h1', {}, 'Let’s reconnect.'), h('p', {}, error.message),
      h('button', {type: 'button', onClick: start}, 'Try again'));
  }
}
document.querySelector('#new-plan').addEventListener('click', () => {
  if (state.busy) return;
  state.plan = null; state.ideas = null; render(); document.querySelector('#title').focus();
});
document.querySelector('#cancel-delete').addEventListener('click', () => dialog.close());
document.querySelector('#confirm-delete').addEventListener('click', deletePlan);
start();
