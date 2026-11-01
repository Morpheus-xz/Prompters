/** Pure schedule views receive the date at the application boundary. */
/** @import {PlanDetail, Task} from "../../types/contracts.js" */
import { h, section, date } from '../dom.js';

/**
 * @param {Task} task
 * @param {string} today
 * @param {(id: string, done: boolean) => void} onToggle
 */
function taskRow(task, today, onToggle) {
  const checkbox = h('input', { type: 'checkbox', id: task.id, checked: task.done });
  checkbox.addEventListener('change', () => onToggle(task.id, checkbox.checked));
  const overdue = task.due_date < today && !task.done;
  return h(
    'li',
    {},
    checkbox,
    h('label', { for: task.id }, task.title),
    h('time', { datetime: task.due_date }, date(task.due_date)),
    overdue ? h('span', { className: 'badge over' }, 'Overdue') : null,
  );
}

/**
 * @param {PlanDetail} plan
 * @param {(id: string, done: boolean) => void} onToggle
 * @param {string} today
 */
export function timelineView(plan, onToggle, today) {
  const { tasks_done, tasks_total, overdue_count } = plan.progress;
  const notice = plan.timeline_compressed
    ? h(
        'p',
        { className: 'notice' },
        'Your event is soon, so we compressed the schedule.',
      )
    : null;
  return section(
    'timeline',
    '02',
    'Timeline',
    'One step at a time, all the way to the day.',
    notice,
    h(
      'p',
      { className: 'muted' },
      `${tasks_done} of ${tasks_total} tasks complete · ${overdue_count} overdue`,
    ),
    h(
      'ul',
      { className: 'checklist' },
      plan.tasks.map((task) => taskRow(task, today, onToggle)),
    ),
  );
}
