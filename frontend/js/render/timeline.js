/** Pure schedule rendering with native accessible checkboxes. */
import {h, section, date} from '../dom.js';

/** Display scheduled dates and completion state. */
export function timelineView(plan, onToggle) {
  const today = new Date().toLocaleDateString('en-CA');
  return section('timeline', '02', 'Timeline', 'One step at a time, all the way to the day.',
    plan.timeline_compressed ? h('p', {className: 'notice'}, 'Your event is soon, so we compressed the schedule.') : null,
    h('p', {className: 'muted'}, `${plan.progress.tasks_done} of ${plan.progress.tasks_total} tasks complete · ${plan.progress.overdue_count} overdue`),
    h('ul', {className: 'checklist'}, plan.tasks.map(task => h('li', {},
      h('input', {type: 'checkbox', id: task.id, checked: task.done, onChange: event => onToggle(task.id, event.target.checked)}),
      h('label', {for: task.id}, task.title), h('time', {datetime: task.due_date}, date(task.due_date)),
      task.due_date < today && !task.done ? h('span', {className: 'badge over'}, 'Overdue') : null))));
}
