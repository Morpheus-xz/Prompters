/** Pure budget and expense form rendering. */
import {h, field, select, section, money} from '../dom.js';

/** Show numeric balances, explicit health labels and expense controls. */
export function budgetView(plan, onAdd, onRemove) {
  const labels = {on_track: '✓ On track', warning: '△ Nearing limit', over: '! Over budget'};
  const rows = plan.budget.lines.map(line => h('tr', {}, h('th', {scope: 'row'}, line.label),
    ...[line.allocated, line.spent, line.remaining].map(v => h('td', {}, money(v, plan.currency))),
    h('td', {}, h('meter', {min: 0, max: 100, value: Math.min(line.percent_used, 100),
      'aria-label': `${line.label}: ${line.percent_used}% used`}),
    h('span', {className: `badge ${line.state}`}, labels[line.state]))));
  const form = h('form', {id: 'expense-form', onSubmit: onAdd}, h('div', {className: 'expense-fields'},
    field('category', 'Category', select(plan.budget.lines.map(l => [l.category, l.label]), plan.budget.lines[0].category)),
    field('amount', 'Amount', h('input', {type: 'number', min: 0.01, max: 1000000000, step: '0.01', required: true})),
    field('description', 'Description', h('input', {required: true, maxlength: 120, placeholder: 'e.g. Venue deposit'}))),
    h('button', {type: 'submit'}, '＋ Log expense'));
  return section('budget', '01', 'Budget', 'Every detail has its place. Every expense, accounted for.',
    h('div', {className: 'metrics'}, ...[['Total budget', plan.total_budget], ['Spent so far', plan.budget.total_spent],
      ['Still available', plan.budget.total_remaining]].map(([label, value]) => h('div', {}, h('small', {}, label), h('strong', {}, money(value, plan.currency))))),
    h('p', {className: `badge ${plan.budget.state}`}, labels[plan.budget.state]),
    h('p', {className: 'muted'}, `${money(plan.per_guest_budget, plan.currency)} per guest · indicative allocation`),
    h('div', {className: 'table-wrap', tabindex: '0', 'aria-label': 'Budget category balances'}, h('table', {},
      h('caption', {className: 'sr-only'}, 'Allocated, spent and remaining by category'),
      h('thead', {}, h('tr', {}, ['Category', 'Allocated', 'Spent', 'Remaining', 'Status'].map(v => h('th', {scope: 'col'}, v)))), h('tbody', {}, rows))),
    h('h4', {}, 'Log an expense'), form,
    h('ul', {className: 'expense-list'}, plan.expenses.map(expense => h('li', {},
      h('span', {}, `${expense.description} · ${money(expense.amount, plan.currency)}`),
      h('button', {type: 'button', 'aria-label': `Remove expense: ${expense.description}`, onClick: () => onRemove(expense.id)}, 'Remove')))));
}
