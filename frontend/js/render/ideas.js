/** Group validated creative text by the categories already present in the plan. */
/** @import {Idea, IdeaFocus, IdeasResponse, PlanDetail} from "../../types/contracts.js" */
import { h, field, select, section } from '../dom.js';
import { IDEA_FOCUSES } from '../config.js';

/** @typedef {(focus: IdeaFocus, refresh: boolean) => void} GenerateIdeas */

/** @param {Idea} idea */
function ideaCard(idea) {
  return h(
    'article',
    { className: 'idea-card' },
    h('span', { className: 'badge' }, `${idea.cost_level} cost`),
    h('h5', {}, idea.title),
    h('p', {}, idea.description),
  );
}

/**
 * @param {string} label
 * @param {Idea[]} ideas
 */
function categoryGroup(label, ideas) {
  if (!ideas.length) return null;
  return h(
    'div',
    { className: 'idea-group' },
    h('h4', {}, label),
    h('div', { className: 'idea-grid' }, ideas.map(ideaCard)),
  );
}

/**
 * @param {IdeasResponse | null} result
 * @param {GenerateIdeas} onGenerate
 */
function ideaControls(result, onGenerate) {
  const focus = select(IDEA_FOCUSES, result?.focus || 'overall');
  const selectedFocus = () => /** @type {IdeaFocus} */ (focus.value);
  return h(
    'div',
    { className: 'ideas-controls' },
    field('focus', 'I’d like ideas for', focus),
    h(
      'button',
      {
        type: 'button',
        className: 'primary',
        onClick: () => onGenerate(selectedFocus(), false),
      },
      '✧ Generate ideas',
    ),
    h(
      'button',
      { type: 'button', onClick: () => onGenerate(selectedFocus(), true) },
      'Refresh',
    ),
  );
}

/**
 * @param {PlanDetail} plan
 * @param {IdeasResponse | null} result
 */
function ideaResults(plan, result) {
  if (!result) {
    return h(
      'p',
      { className: 'empty-ideas' },
      'The practical pieces are in place. Let’s add a little personality.',
    );
  }
  const groups = plan.budget.lines.map((line) =>
    categoryGroup(
      line.label,
      result.ideas.filter((idea) => idea.budget_category === line.category),
    ),
  );
  const notice = result.from_cache
    ? 'Saved ideas · refresh for new inspiration.'
    : 'Fresh inspiration for your celebration.';
  return h(
    'div',
    {},
    h('p', { className: 'notice' }, notice),
    groups,
    h(
      'p',
      { className: 'pro-tip' },
      h('strong', {}, 'A thoughtful tip: '),
      result.pro_tip,
    ),
  );
}

/**
 * @param {PlanDetail} plan
 * @param {IdeasResponse | null} result
 * @param {GenerateIdeas} onGenerate
 */
export function ideasView(plan, result, onGenerate) {
  return section(
    'ideas',
    '04',
    'Ideas for you',
    'A little inspiration, grounded in your actual plan.',
    ideaControls(result, onGenerate),
    h(
      'p',
      { className: 'muted' },
      'Gemini adds creative suggestions. Your budget and schedule are calculated by Festiva.',
    ),
    ideaResults(plan, result),
  );
}
