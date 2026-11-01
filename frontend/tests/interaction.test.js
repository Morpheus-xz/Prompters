import assert from 'node:assert/strict';
import { beforeEach, test } from 'node:test';
import { ApiError } from '../js/api.js';
import { runAction } from '../js/ui.js';
import { state } from '../js/state.js';
import { createForm } from '../js/render/create-plan.js';
import { planInput, expenseInput } from '../js/forms.js';
import { eventTypes, installDom } from './helpers.js';

beforeEach(() => {
  installDom(
    '<div id="workspace"><button id="save">Save</button><input id="title"><span id="title-error"></span></div><div id="status"></div>',
  );
  state.busy = false;
});

test('pending actions serialize requests and expose loading state', async () => {
  let complete;
  const operation = new Promise((resolve) => {
    complete = resolve;
  });
  let renders = 0;
  document.getElementById('save').focus();
  const pending = runAction(
    () => operation,
    'Saved',
    () => {
      renders += 1;
    },
  );
  assert.equal(state.busy, true);
  assert.equal(document.getElementById('save').disabled, true);
  assert.equal(document.getElementById('workspace').getAttribute('aria-busy'), 'true');
  assert.equal(
    await runAction(
      async () => {},
      'Duplicate',
      () => {},
    ),
    false,
  );
  complete();
  assert.equal(await pending, true);
  assert.equal(renders, 1);
  assert.equal(state.busy, false);
  assert.equal(document.activeElement.id, 'save');
  assert.equal(document.getElementById('status').textContent, 'Saved');
});

test('failed actions restore controls and expose field errors without rerendering', async () => {
  const error = new ApiError('Check title', [{ field: 'title', message: 'Required' }]);
  const success = await runAction(
    async () => {
      throw error;
    },
    'Saved',
    () => {
      assert.fail('Unexpected render');
    },
  );
  assert.equal(success, false);
  assert.equal(state.busy, false);
  assert.equal(document.getElementById('save').disabled, false);
  assert.equal(document.getElementById('title').getAttribute('aria-invalid'), 'true');
  assert.equal(document.getElementById('title-error').textContent, 'Required');
});

test('form extraction converts numeric fields and normalizes optional blanks', () => {
  const view = createForm(eventTypes(), () => {});
  const form = view.querySelector('form');
  form.querySelector('#title').value = ' Birthday ';
  form.querySelector('#event_date').value = '2027-01-10';
  form.querySelector('#total_budget').value = '100.01';
  form.querySelector('#city').value = '   ';
  const input = planInput(form);
  assert.equal(input.title, 'Birthday');
  assert.equal(input.total_budget, 100.01);
  assert.equal(input.guest_count, 50);
  assert.equal(input.city, null);
  assert.equal(input.preferences, null);
});

test('expense form extraction follows the same numeric contract', () => {
  const dom = installDom(
    '<form><input name="category" value="venue"><input name="amount" value="12.34"><input name="description" value=" Deposit "></form>',
  );
  assert.deepEqual(expenseInput(dom.window.document.querySelector('form')), {
    category: 'venue',
    amount: 12.34,
    description: 'Deposit',
  });
});
