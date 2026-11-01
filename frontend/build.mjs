/** Package unchanged static assets and an environment-specific Vercel proxy. */
import {cp, mkdir, writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const frontend = fileURLToPath(new URL('.', import.meta.url));
const securityHeaders = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
};

/** @param {string} value Public Render HTTPS origin, without paths or credentials. */
export function backendOrigin(value) {
  if (!value) throw new Error('Set BACKEND_URL to the Render service HTTPS origin.');
  const url = new URL(value);
  if (url.protocol !== 'https:' || url.username || url.password ||
      url.pathname !== '/' || url.search || url.hash) {
    throw new Error('BACKEND_URL must be an HTTPS origin without credentials, path, query or fragment.');
  }
  return url.origin;
}

/** @param {string} value Build-time backend URL; never a Gemini key. */
export function deploymentConfig(value) {
  const origin = backendOrigin(value);
  return {
    version: 3,
    routes: [
      {src: '^/(.*)$', headers: securityHeaders, continue: true},
      {src: '^/(plans(?:/.*)?|event-types|health)$', dest: `${origin}/$1`,
        headers: {'Cache-Control': 'no-store'}},
      {src: '^/static/(.*)$', headers: {'Cache-Control': 'public, max-age=3600'}, continue: true},
      {src: '^/$', headers: {'Cache-Control': 'no-cache'}, continue: true},
      {handle: 'filesystem'},
    ],
  };
}

/** @param {string} value Public backend origin. @param {string} output Artifact directory. */
export async function build(value, output = resolve(frontend, '.vercel/output')) {
  const config = deploymentConfig(value);
  const assets = resolve(output, 'static');
  await mkdir(resolve(assets, 'static'), {recursive: true});
  await cp(resolve(frontend, 'index.html'), resolve(assets, 'index.html'));
  for (const directory of ['css', 'js']) {
    await cp(resolve(frontend, directory), resolve(assets, 'static', directory), {recursive: true});
  }
  await writeFile(resolve(output, 'config.json'), `${JSON.stringify(config, null, 2)}\n`);
}

if (process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url) {
  await build(process.env.BACKEND_URL);
}
