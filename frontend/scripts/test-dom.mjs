import { resolve } from 'node:path';
import { build } from 'esbuild';
import { spawnSync } from 'node:child_process';
import { mkdirSync, rmSync } from 'node:fs';
const dir = 'node_modules/.cache/qa-dom-tests';
mkdirSync(dir, {recursive:true});
try {
  await build({entryPoints:['unit/workspace.test.tsx'], outfile:`${dir}/tests.mjs`, bundle:true, platform:'node', format:'esm', packages:'external', jsx:'automatic'});
  const result = spawnSync(process.execPath, ['--test', resolve(`${dir}/tests.mjs`)], {stdio:'inherit'});
  process.exitCode = result.status ?? 1;
} finally { rmSync(dir, {recursive:true, force:true}); }
