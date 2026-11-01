/** Pure creative ideas rendering, grouped by allocated category. */
import {h, field, select, section} from '../dom.js';

/** Show grounded generation controls and validated suggestions. */
export function ideasView(plan, result, onGenerate) {
  const focuses = ['overall', 'theme', 'food', 'entertainment', 'decor', 'activities', 'saving_money'];
  const focus = select(focuses.map(v => [v, v.replaceAll('_', ' ')]), result?.focus || 'overall');
  const groups = plan.budget.lines.map(line => {
    const items = result?.ideas.filter(idea => idea.budget_category === line.category) || [];
    return items.length ? h('div', {className: 'idea-group'}, h('h4', {}, line.label),
      h('div', {className: 'idea-grid'}, items.map(idea => h('article', {className: 'idea-card'},
        h('span', {className: 'badge'}, `${idea.cost_level} cost`), h('h5', {}, idea.title), h('p', {}, idea.description))))) : null;
  });
  return section('ideas', '04', 'Ideas for you', 'A little inspiration, grounded in your actual plan.',
    h('div', {className: 'ideas-controls'}, field('focus', 'I’d like ideas for', focus),
      h('button', {type: 'button', className: 'primary', onClick: () => onGenerate(focus.value, false)}, '✧ Generate ideas'),
      h('button', {type: 'button', onClick: () => onGenerate(focus.value, true)}, 'Refresh')),
    h('p', {className: 'muted'}, 'Gemini adds creative suggestions. Your budget and schedule are calculated by Festiva.'),
    result ? h('div', {}, h('p', {className: 'notice'}, result.from_cache ? 'Saved ideas · refresh for new inspiration.' : 'Fresh inspiration for your celebration.'), groups,
      h('p', {className: 'pro-tip'}, h('strong', {}, 'A thoughtful tip: '), result.pro_tip))
      : h('p', {className: 'empty-ideas'}, 'The practical pieces are in place. Let’s add a little personality.'));
}
