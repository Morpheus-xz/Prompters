/** Pure booking checklist with native, explicitly labeled controls. */
/** @import {PlanDetail, Vendor, VendorStatus} from "../../types/contracts.js" */
import { h, section, select } from '../dom.js';
import { VENDOR_STATUSES } from '../config.js';

/**
 * @param {Vendor} vendor
 * @param {(id: string, status: VendorStatus) => void} onUpdate
 */
function vendorRow(vendor, onUpdate) {
  const control = select(VENDOR_STATUSES, vendor.status, { id: vendor.id });
  control.addEventListener('change', () =>
    onUpdate(vendor.id, /** @type {VendorStatus} */ (control.value)),
  );
  const essential = vendor.essential
    ? h('span', { className: 'badge' }, 'Essential')
    : null;
  return h('li', {}, h('label', { for: vendor.id }, vendor.name, essential), control);
}

/**
 * @param {PlanDetail} plan
 * @param {(id: string, status: VendorStatus) => void} onUpdate
 */
export function vendorsView(plan, onUpdate) {
  const { essential_vendors_booked, essential_vendors_total } = plan.progress;
  return section(
    'vendors',
    '03',
    'Vendor checklist',
    'The people who help bring it all together.',
    h(
      'p',
      { className: 'muted' },
      `${essential_vendors_booked} of ${essential_vendors_total} essential vendors booked`,
    ),
    h(
      'ul',
      { className: 'vendor-list' },
      plan.vendors.map((vendor) => vendorRow(vendor, onUpdate)),
    ),
  );
}
