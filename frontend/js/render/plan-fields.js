/** Small field groups keep the event brief readable without a UI framework. */
import { field, h, select } from '../dom.js';
import { CURRENCIES, FORM_LIMITS } from '../config.js';
import { moneyField } from '../forms.js';

/** @param {HTMLSelectElement} type */
export function identityFields(type) {
  const title = h('input', {
    required: true,
    maxlength: FORM_LIMITS.title,
    placeholder: 'e.g. Maya & Arjun’s wedding',
  });
  return [
    field('title', 'What are we celebrating?', title, 'Give your celebration a name.'),
    field(
      'event_type',
      'Event type',
      type,
      'A practical starting point, tailored to your event.',
    ),
  ];
}

/** Render date and headcount inputs with their original validation hints. */
export function scheduleFields() {
  const eventDate = h('input', { type: 'date', required: true });
  const guests = h('input', {
    type: 'number',
    min: 1,
    max: FORM_LIMITS.guests,
    required: true,
    value: FORM_LIMITS.defaultGuests,
  });
  return [
    field(
      'event_date',
      'Event date',
      eventDate,
      'Choose a future date within five years.',
    ),
    field(
      'guest_count',
      'Number of guests',
      guests,
      'Include everyone you expect to host.',
    ),
  ];
}

/** Share the money input policy with expense entry. */
export function budgetFields() {
  const currency = select(
    CURRENCIES.map((value) => [value, value]),
    'INR',
  );
  return [
    moneyField(
      'total_budget',
      'Total budget',
      'We’ll allocate every last cent.',
      '100000',
    ),
    field('currency', 'Currency', currency, 'One currency throughout your plan.'),
  ];
}

/** Render optional personalization fields; blank values become null on submit. */
export function personalFields() {
  const city = h('input', {
    maxlength: FORM_LIMITS.city,
    placeholder: 'Where people come together',
  });
  const preferences = h('textarea', {
    maxlength: FORM_LIMITS.preferences,
    rows: 3,
    placeholder: 'A garden setting, vegetarian food, a love of live music…',
  });
  return [
    field('city', 'City (optional)', city),
    field(
      'preferences',
      'Make it yours (optional)',
      preferences,
      'Interests, traditions, dietary needs or accessibility preferences.',
    ),
  ];
}
