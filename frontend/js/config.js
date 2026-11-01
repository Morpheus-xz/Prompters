/** Browser presentation policy; all financial calculations remain on the server. */
/** @import {BudgetState, Choice} from "../types/contracts.js" */
export const FORM_LIMITS = Object.freeze({
  title: 80,
  city: 60,
  preferences: 300,
  expenseDescription: 120,
  guests: 5000,
  budget: 1000000000,
  moneyStep: 0.01,
  defaultGuests: 50,
});
export const CURRENCIES = ['INR', 'USD', 'EUR', 'GBP'];
export const PLAN_SECTIONS = [
  ['budget', 'Budget'],
  ['timeline', 'Timeline'],
  ['vendors', 'Vendor checklist'],
  ['ideas', 'Ideas for you'],
];
/** @type {Readonly<Record<BudgetState, string>>} */
export const BUDGET_LABELS = Object.freeze({
  on_track: '✓ On track',
  warning: '△ Nearing limit',
  over: '! Over budget',
});
/** @type {readonly Choice[]} */
export const VENDOR_STATUSES = [
  ['to_contact', 'To contact'],
  ['contacted', 'Contacted'],
  ['booked', 'Booked'],
];
/** @type {readonly Choice[]} */
export const IDEA_FOCUSES = [
  ['overall', 'overall'],
  ['theme', 'theme'],
  ['food', 'food'],
  ['entertainment', 'entertainment'],
  ['decor', 'decor'],
  ['activities', 'activities'],
  ['saving_money', 'saving money'],
];
