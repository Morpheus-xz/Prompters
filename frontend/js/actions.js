/** API orchestration and state transitions, independent of DOM rendering. */
/** @import {AppState, CreatePlanInput, EventTypeInfo, ExpenseInput, IdeaFocus, PlanDetail, PlanSummary, VendorStatus} from "../types/contracts.js" */
import { api } from './api.js';
import { state, selectPlan, rememberPlan, discardPlan } from './state.js';

/** Apply authoritative responses to one store; renderers never issue requests. */
export class PlanActions {
  /**
   * @param {typeof api} [request]
   * @param {AppState} [store]
   */
  constructor(request = api, store = state) {
    this.request = request;
    this.store = store;
  }

  /** Load both resources before publishing initial UI state. */
  async loadInitialState() {
    /** @type {EventTypeInfo[]} */
    const types = await this.request('/event-types');
    /** @type {PlanSummary[]} */
    const plans = await this.request('/plans');
    this.store.types = types;
    this.store.plans = plans;
  }

  /** @param {string} id */
  async openPlan(id) {
    /** @type {PlanDetail} */
    const plan = await this.request(`/plans/${id}`);
    selectPlan(plan, this.store);
  }

  /** @param {CreatePlanInput} input */
  async createPlan(input) {
    /** @type {PlanDetail} */
    const plan = await this.request('/plans', 'POST', input);
    rememberPlan(plan, this.store);
  }

  /** @param {string} [suffix] */
  #planPath(suffix = '') {
    if (!this.store.plan) throw new Error('Select a plan before updating it.');
    return `/plans/${this.store.plan.id}${suffix}`;
  }

  /**
   * @param {string} suffix
   * @param {string} method
   * @param {object} [body]
   */
  async #updatePlan(suffix, method, body) {
    this.store.plan = await this.request(this.#planPath(suffix), method, body);
  }

  /** @param {ExpenseInput} input */
  async addExpense(input) {
    await this.#updatePlan('/expenses', 'POST', input);
  }

  /** @param {string} id */
  async removeExpense(id) {
    await this.#updatePlan(`/expenses/${id}`, 'DELETE');
  }

  /**
   * @param {string} id
   * @param {boolean} done
   */
  async updateTask(id, done) {
    await this.#updatePlan(`/tasks/${id}`, 'PATCH', { done });
  }

  /**
   * @param {string} id
   * @param {VendorStatus} status
   */
  async updateVendor(id, status) {
    await this.#updatePlan(`/vendors/${id}`, 'PATCH', { status });
  }

  /**
   * @param {IdeaFocus} focus
   * @param {boolean} refresh
   */
  async generateIdeas(focus, refresh) {
    this.store.ideas = await this.request(this.#planPath('/ideas'), 'POST', {
      focus,
      refresh,
    });
  }

  /** Clear state only after the server accepts deletion. */
  async deletePlan() {
    const id = this.store.plan?.id;
    await this.request(this.#planPath(), 'DELETE');
    if (id) discardPlan(id, this.store);
  }
}

export const actions = new PlanActions();
