/** Real DOM fixtures and isolated client state; no browser network is used. */
import { JSDOM } from 'jsdom';

/** Install the DOM interfaces used by the vanilla UI. */
export function installDom(
  html = '<div id="workspace"></div><div id="status" role="status"></div>',
) {
  const dom = new JSDOM(html, { url: 'https://festiva.test/' });
  for (const name of [
    'document',
    'Node',
    'HTMLElement',
    'HTMLInputElement',
    'HTMLSelectElement',
    'HTMLTextAreaElement',
    'HTMLButtonElement',
    'HTMLDialogElement',
    'FormData',
    'Event',
  ]) {
    globalThis[name] = dom.window[name];
  }
  return dom;
}

/** A detached store makes action tests independent of application globals. */
export function emptyState() {
  return { types: [], plans: [], plan: null, ideas: null, busy: false };
}

/** Minimal realistic server response shared by view and action tests. */
const samplePlan = {
  id: 'plan-1',
  title: 'A joyful day',
  event_type: 'wedding',
  event_date: '2027-01-10',
  guest_count: 50,
  total_budget: 10000,
  currency: 'INR',
  city: 'Pune',
  preferences: null,
  created_at: '2026-01-01T00:00:00Z',
  timeline_compressed: true,
  allocations: { venue: 2500, catering: 7500 },
  per_guest_budget: 200,
  budget: {
    lines: [
      {
        category: 'venue',
        label: 'Venue',
        allocated: 2500,
        spent: 2600,
        remaining: -100,
        percent_used: 104,
        state: 'over',
      },
      {
        category: 'catering',
        label: 'Food & catering',
        allocated: 7500,
        spent: 0,
        remaining: 7500,
        percent_used: 0,
        state: 'on_track',
      },
    ],
    total_allocated: 10000,
    total_spent: 2600,
    total_remaining: 7400,
    percent_used: 26,
    state: 'on_track',
  },
  progress: {
    tasks_total: 1,
    tasks_done: 0,
    overdue_count: 1,
    essential_vendors_total: 1,
    essential_vendors_booked: 0,
    readiness_score: 0,
    days_until_event: 9,
  },
  tasks: [
    {
      id: 'task-01',
      title: 'Book venue',
      category: 'venue',
      due_date: '2026-01-01',
      done: false,
    },
  ],
  vendors: [
    {
      id: 'vendor-01',
      name: 'Venue',
      category: 'venue',
      essential: true,
      status: 'to_contact',
    },
  ],
  expenses: [
    {
      id: 'expense-1',
      category: 'venue',
      amount: 2600,
      description: 'Deposit',
      logged_at: '2026-01-01T00:00:00Z',
    },
  ],
};

/** Return detached data so interactions cannot mutate another test’s fixture. */
export function planFixture() {
  return structuredClone(samplePlan);
}

/** Registry-shaped choices for the create form’s live allocation preview. */
export function eventTypes() {
  return [
    {
      key: 'wedding',
      label: 'Wedding',
      description: 'Wedding plan',
      budget_split: [
        { category: 'venue', label: 'Venue', percent: 25 },
        { category: 'catering', label: 'Food & catering', percent: 75 },
      ],
    },
    {
      key: 'birthday',
      label: 'Birthday',
      description: 'Birthday plan',
      budget_split: [
        { category: 'venue', label: 'Venue', percent: 20 },
        { category: 'catering', label: 'Food & catering', percent: 80 },
      ],
    },
  ];
}
