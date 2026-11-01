import assert from 'node:assert/strict';
import test from 'node:test';
import { api, ApiError } from '../js/api.js';

/** Injected transport records wire data without replacing the global fetch. */
test('requests serialize JSON and retain same-origin cookie credentials', async () => {
  let sent;
  const transport = async (path, options) => {
    sent = { path, ...options };
    return Response.json({ id: 'plan-1' });
  };
  assert.deepEqual(await api('/plans', 'POST', { title: 'Party' }, transport), {
    id: 'plan-1',
  });
  assert.equal(sent.path, '/plans');
  assert.equal(sent.credentials, 'same-origin');
  assert.equal(sent.headers['Content-Type'], 'application/json');
  assert.equal(sent.body, '{"title":"Party"}');
});

test('204 responses require no JSON body', async () => {
  const transport = async () => new Response(null, { status: 204 });
  assert.equal(await api('/plans/id', 'DELETE', undefined, transport), null);
});

test('422 validation errors expose normalized field errors', async () => {
  const transport = async () =>
    Response.json(
      { detail: [{ loc: ['body', 'guest_count'], msg: 'Must be positive' }] },
      { status: 422 },
    );
  await assert.rejects(api('/plans', 'POST', {}, transport), (error) => {
    assert.ok(error instanceof ApiError);
    assert.deepEqual(error.fields, [
      { field: 'guest_count', message: 'Must be positive' },
    ]);
    return true;
  });
});

test('429 responses provide a readable retry message', async () => {
  const transport = async () => Response.json({ detail: 'rate' }, { status: 429 });
  await assert.rejects(api('/plans', 'GET', undefined, transport), /wait a minute/);
});

test('HTML proxy failures become a safe actionable response error', async () => {
  const transport = async () => new Response('<html>upstream</html>', { status: 502 });
  await assert.rejects(
    api('/plans', 'GET', undefined, transport),
    /unexpected response/,
  );
});

test('connection errors are mapped at the network boundary', async () => {
  const transport = async () => {
    throw new TypeError('private socket detail');
  };
  await assert.rejects(api('/plans', 'GET', undefined, transport), /Connection lost/);
});

test('generic error bodies and empty details have stable messages', async () => {
  for (const [body, expected] of [
    [{ detail: 'Not found.' }, /Not found/],
    [{}, /Something went wrong/],
  ]) {
    const transport = async () => Response.json(body, { status: 404 });
    await assert.rejects(api('/plans', 'GET', undefined, transport), expected);
  }
});
