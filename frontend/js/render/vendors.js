/** Pure booking checklist rendering. */
import {h, section, select} from '../dom.js';

/** Display essential and optional providers with booking stages. */
export function vendorsView(plan, onUpdate) {
  const options = [['to_contact', 'To contact'], ['contacted', 'Contacted'], ['booked', 'Booked']];
  return section('vendors', '03', 'Vendor checklist', 'The people who help bring it all together.',
    h('p', {className: 'muted'}, `${plan.progress.essential_vendors_booked} of ${plan.progress.essential_vendors_total} essential vendors booked`),
    h('ul', {className: 'vendor-list'}, plan.vendors.map(vendor => h('li', {},
      h('label', {for: vendor.id}, vendor.name, vendor.essential ? h('span', {className: 'badge'}, 'Essential') : null),
      select(options, vendor.status, {id: vendor.id, onChange: event => onUpdate(vendor.id, event.target.value)})))));
}
