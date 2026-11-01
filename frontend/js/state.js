/** Client state and transitions that must update selection and ideas together. */
/** @import {AppState, PlanDetail} from "../types/contracts.js" */
/** @type {AppState} */
export const state = { types: [], plans: [], plan: null, ideas: null, busy: false };

/**
 * @param {PlanDetail | null} plan
 * @param {AppState} [store]
 */
export function selectPlan(plan, store = state) {
  store.plan = plan;
  store.ideas = null;
}

/**
 * @param {PlanDetail} plan
 * @param {AppState} [store]
 */
export function rememberPlan(plan, store = state) {
  store.plans = [
    ...store.plans,
    {
      id: plan.id,
      title: plan.title,
      event_type: plan.event_type,
      event_date: plan.event_date,
    },
  ];
  selectPlan(plan, store);
}

/**
 * @param {string} id
 * @param {AppState} [store]
 */
export function discardPlan(id, store = state) {
  store.plans = store.plans.filter((plan) => plan.id !== id);
  selectPlan(null, store);
}
