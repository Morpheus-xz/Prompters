/** Present server-computed balances; no arithmetic is repeated in the UI. */
/** @import {BudgetLine, PlanDetail} from "../../types/contracts.js" */
import { h, section, money } from '../dom.js';
import { BUDGET_LABELS } from '../config.js';
import { expenseForm, expenseHistory } from './expenses.js';

/** @param {PlanDetail} plan */
function metrics(plan) {
  /** @type {[string, number][]} */
  const values = [
    ['Total budget', plan.total_budget],
    ['Spent so far', plan.budget.total_spent],
    ['Still available', plan.budget.total_remaining],
  ];
  return h(
    'div',
    { className: 'metrics' },
    values.map(([label, value]) =>
      h('div', {}, h('small', {}, label), h('strong', {}, money(value, plan.currency))),
    ),
  );
}

/**
 * @param {BudgetLine} line
 * @param {string} currency
 */
function budgetRow(line, currency) {
  const balances = [line.allocated, line.spent, line.remaining].map((value) =>
    h('td', {}, money(value, currency)),
  );
  const meter = h('meter', {
    min: 0,
    max: 100,
    value: Math.min(line.percent_used, 100),
    'aria-label': `${line.label}: ${line.percent_used}% used`,
  });
  const status = h(
    'span',
    { className: `badge ${line.state}` },
    BUDGET_LABELS[line.state],
  );
  return h(
    'tr',
    {},
    h('th', { scope: 'row' }, line.label),
    balances,
    h('td', {}, meter, status),
  );
}

/** @param {PlanDetail} plan */
function budgetTable(plan) {
  const labels = ['Category', 'Allocated', 'Spent', 'Remaining', 'Status'];
  const headings = labels.map((label) => h('th', { scope: 'col' }, label));
  const header = h('thead', {}, h('tr', {}, headings));
  const rows = h(
    'tbody',
    {},
    plan.budget.lines.map((line) => budgetRow(line, plan.currency)),
  );
  const table = h(
    'table',
    {},
    h(
      'caption',
      { className: 'sr-only' },
      'Allocated, spent and remaining by category',
    ),
    header,
    rows,
  );
  return h(
    'div',
    {
      className: 'table-wrap',
      tabindex: '0',
      'aria-label': 'Budget category balances',
    },
    table,
  );
}

/**
 * @param {PlanDetail} plan
 * @param {(form: HTMLFormElement) => void} onAdd
 * @param {(id: string) => void} onRemove
 */
export function budgetView(plan, onAdd, onRemove) {
  return section(
    'budget',
    '01',
    'Budget',
    'Every detail has its place. Every expense, accounted for.',
    metrics(plan),
    h(
      'p',
      { className: `badge ${plan.budget.state}` },
      BUDGET_LABELS[plan.budget.state],
    ),
    h(
      'p',
      { className: 'muted' },
      `${money(plan.per_guest_budget, plan.currency)} per guest · indicative allocation`,
    ),
    budgetTable(plan),
    h('h4', {}, 'Log an expense'),
    expenseForm(plan, onAdd),
    expenseHistory(plan, onRemove),
  );
}
