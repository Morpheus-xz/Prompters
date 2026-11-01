/** Owner-scoped plan navigation and the dashboard’s descriptive header. */
/** @import {PlanDetail, PlanSummary} from "../../types/contracts.js" */
import { h, date } from '../dom.js';
import { PLAN_SECTIONS } from '../config.js';

/**
 * @param {PlanSummary} plan
 * @param {string | undefined} current
 * @param {(id: string) => void} onOpen
 */
function planButton(plan, current, onOpen) {
  return h(
    'button',
    {
      type: 'button',
      className: plan.id === current ? 'selected' : '',
      'aria-current': plan.id === current ? 'true' : null,
      onClick: () => onOpen(plan.id),
    },
    h('strong', {}, plan.title),
    h('small', {}, date(plan.event_date)),
  );
}

/**
 * @param {PlanSummary[]} plans
 * @param {string | undefined} current
 * @param {(id: string) => void} onOpen
 */
export function planList(plans, current, onOpen) {
  if (!plans.length) {
    return h('p', { className: 'muted' }, 'Your next good memory starts here.');
  }
  return h(
    'ul',
    { className: 'plan-list' },
    plans.map((plan) => h('li', {}, planButton(plan, current, onOpen))),
  );
}

/**
 * @param {PlanDetail} plan
 * @param {() => void} onDelete
 */
function titleRow(plan, onDelete) {
  return h(
    'div',
    { className: 'title-row' },
    h('h1', { id: 'plan-heading', tabindex: '-1' }, plan.title),
    h(
      'button',
      { type: 'button', className: 'quiet', onClick: onDelete },
      'Delete plan',
    ),
  );
}

/** @param {PlanDetail} plan */
function readiness(plan) {
  const { readiness_score, days_until_event } = plan.progress;
  return h(
    'div',
    { className: 'readiness' },
    h('strong', {}, `${days_until_event} days to go`),
    h('label', { for: 'readiness' }, `${readiness_score}% ready to celebrate`),
    h(
      'progress',
      { id: 'readiness', max: 100, value: readiness_score },
      `${readiness_score}%`,
    ),
  );
}

/**
 * @param {PlanDetail} plan
 * @param {() => void} onDelete
 */
export function planHeader(plan, onDelete) {
  const description = `${plan.event_type} · ${date(plan.event_date)} · ${plan.guest_count} guests`;
  const navigation = h(
    'nav',
    { 'aria-label': 'Plan sections', className: 'section-nav' },
    PLAN_SECTIONS.map(([id, label]) => h('a', { href: `#${id}` }, label)),
  );
  return h(
    'div',
    {},
    h('p', { className: 'eyebrow' }, description),
    titleRow(plan, onDelete),
    readiness(plan),
    navigation,
  );
}
