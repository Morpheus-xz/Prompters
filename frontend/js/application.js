/** Connect actions, pure views and accessible interaction effects in one place. */
/** @import {IdeaFocus, VendorStatus} from "../types/contracts.js" */
import { h } from './dom.js';
import { selectPlan } from './state.js';
import { announce, runAction } from './ui.js';
import { expenseInput, planInput } from './forms.js';
import { createForm } from './render/create-plan.js';
import { planList, planHeader } from './render/plans.js';
import { budgetView } from './render/budget.js';
import { timelineView } from './render/timeline.js';
import { vendorsView } from './render/vendors.js';
import { ideasView } from './render/ideas.js';

/** Coordinate interactions without owning financial or scheduling rules. */
export class PlannerApp {
  /** @param {import('./actions.js').PlanActions} actions */
  constructor(actions) {
    this.actions = actions;
    this.store = actions.store;
    this.workspace = /** @type {HTMLElement} */ (document.getElementById('workspace'));
    this.dialog = /** @type {HTMLDialogElement} */ (
      document.getElementById('delete-dialog')
    );
    document
      .getElementById('new-plan')
      ?.addEventListener('click', () => this.newPlan());
    document
      .getElementById('cancel-delete')
      ?.addEventListener('click', () => this.dialog.close());
    document.getElementById('confirm-delete')?.addEventListener('click', () => {
      void this.deletePlan();
    });
  }

  /** Render exclusively from the latest server responses. */
  render() {
    const { plan, plans, types, ideas } = this.store;
    document
      .getElementById('plans')
      ?.replaceChildren(planList(plans, plan?.id, (id) => this.openPlan(id)));
    if (!plan) {
      this.workspace.replaceChildren(
        createForm(types, (form) => this.createPlan(form)),
      );
      return;
    }
    const today = new Date().toLocaleDateString('en-CA');
    this.workspace.replaceChildren(
      planHeader(plan, () => this.dialog.showModal()),
      h('h2', { className: 'sr-only' }, 'Your event plan'),
      budgetView(
        plan,
        (form) => this.addExpense(form),
        (id) => this.removeExpense(id),
      ),
      timelineView(plan, (id, done) => this.updateTask(id, done), today),
      vendorsView(plan, (id, status) => this.updateVendor(id, status)),
      ideasView(plan, ideas, (focus, refresh) => this.generateIdeas(focus, refresh)),
    );
  }

  /**
   * @param {() => Promise<void>} action
   * @param {string} [message]
   */
  execute(action, message = 'Plan updated.') {
    return runAction(action, message, () => this.render(), this.store);
  }

  /** @param {string} id */
  async openPlan(id) {
    const success = await this.execute(() => this.actions.openPlan(id), 'Plan opened.');
    if (success) document.getElementById('plan-heading')?.focus();
  }

  /**
   * Capture input before loading feedback disables controls.
   * @param {HTMLFormElement} form
   */
  async createPlan(form) {
    const input = planInput(form);
    const success = await this.execute(
      () => this.actions.createPlan(input),
      'Your plan is ready.',
    );
    if (success) document.getElementById('plan-heading')?.focus();
  }

  /** @param {HTMLFormElement} form */
  addExpense(form) {
    const input = expenseInput(form);
    void this.execute(() => this.actions.addExpense(input));
  }

  /** @param {string} id */
  removeExpense(id) {
    void this.execute(() => this.actions.removeExpense(id));
  }

  /**
   * @param {string} id
   * @param {boolean} done
   */
  updateTask(id, done) {
    void this.execute(() => this.actions.updateTask(id, done));
  }

  /**
   * @param {string} id
   * @param {VendorStatus} status
   */
  updateVendor(id, status) {
    void this.execute(() => this.actions.updateVendor(id, status));
  }

  /**
   * @param {IdeaFocus} focus
   * @param {boolean} refresh
   */
  generateIdeas(focus, refresh) {
    void this.execute(() => this.actions.generateIdeas(focus, refresh), 'Ideas ready.');
  }

  /** Keep native confirmation as the deletion entry point. */
  async deletePlan() {
    this.dialog.close();
    const success = await this.execute(
      () => this.actions.deletePlan(),
      'Plan deleted.',
    );
    if (success) document.getElementById('new-plan')?.focus();
  }

  /** Clear selection while retaining the saved sidebar. */
  newPlan() {
    if (this.store.busy) return;
    selectPlan(null, this.store);
    this.render();
    document.getElementById('title')?.focus();
  }

  /** Load initial data and make connection failures actionable. */
  async start() {
    try {
      await this.actions.loadInitialState();
      this.render();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Please try again.';
      announce(message);
      this.workspace.replaceChildren(
        h('h1', {}, 'Let’s reconnect.'),
        h('p', {}, message),
        h(
          'button',
          {
            type: 'button',
            onClick: () => {
              void this.start();
            },
          },
          'Try again',
        ),
      );
    }
  }
}
