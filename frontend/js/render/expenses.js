/** Expense entry and history are independent of budget summary presentation. */
/** @import {Expense, PlanDetail} from "../../types/contracts.js" */
import { h, field, select, money } from '../dom.js';
import { FORM_LIMITS } from '../config.js';
import { moneyField, submitHandler } from '../forms.js';

/** @param {PlanDetail} plan */
function expenseFields(plan) {
  const categories = plan.budget.lines.map(
    (line) => /** @type {[string, string]} */ ([line.category, line.label]),
  );
  const category = select(categories, plan.budget.lines[0].category);
  const description = h('input', {
    required: true,
    maxlength: FORM_LIMITS.expenseDescription,
    placeholder: 'e.g. Venue deposit',
  });
  return [
    field('category', 'Category', category),
    moneyField('amount', 'Amount'),
    field('description', 'Description', description),
  ];
}

/**
 * @param {PlanDetail} plan
 * @param {(form: HTMLFormElement) => void} onAdd
 */
export function expenseForm(plan, onAdd) {
  const form = h(
    'form',
    { id: 'expense-form' },
    h('div', { className: 'expense-fields' }, expenseFields(plan)),
    h('button', { type: 'submit' }, '＋ Log expense'),
  );
  submitHandler(form, onAdd);
  return form;
}

/**
 * @param {Expense} expense
 * @param {string} currency
 * @param {(id: string) => void} onRemove
 */
function expenseRow(expense, currency, onRemove) {
  return h(
    'li',
    {},
    h('span', {}, `${expense.description} · ${money(expense.amount, currency)}`),
    h(
      'button',
      {
        type: 'button',
        'aria-label': `Remove expense: ${expense.description}`,
        onClick: () => onRemove(expense.id),
      },
      'Remove',
    ),
  );
}

/**
 * @param {PlanDetail} plan
 * @param {(id: string) => void} onRemove
 */
export function expenseHistory(plan, onRemove) {
  return h(
    'ul',
    { className: 'expense-list' },
    plan.expenses.map((expense) => expenseRow(expense, plan.currency, onRemove)),
  );
}
