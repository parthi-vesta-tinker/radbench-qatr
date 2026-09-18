import {build} from 'esbuild';
import {spawnSync} from 'node:child_process';
import {readFileSync,writeFileSync,mkdirSync,rmSync} from 'node:fs';
import {resolve} from 'node:path';
const dir=resolve('node_modules/.cache/qa-blueprint');mkdirSync(dir,{recursive:true});
try {
 await build({stdin:{contents:`import React from 'react';import {renderToStaticMarkup} from 'react-dom/server';import App from './src/App';globalThis.sessionStorage={getItem:()=>null};globalThis.localStorage={getItem:()=>null};console.log(renderToStaticMarkup(<App/>));`,resolveDir:process.cwd(),loader:'tsx'},outfile:dir+'/render.mjs',bundle:true,platform:'node',format:'esm',packages:'external',jsx:'automatic'});
 const result=spawnSync(process.execPath,[dir+'/render.mjs'],{encoding:'utf8'});if(result.status)throw Error(result.stderr);
 const markup=result.stdout.trim().replaceAll('<button ','<button disabled ').replaceAll('<textarea ','<textarea disabled ');
 const css=readFileSync('src/style.css','utf8');
 writeFileSync('../prototype/BLUEPRINT.html',`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Vesta QA — Workspace blueprint 1.14</title><style>${css}</style><body><p style="padding:12px 24px;border-bottom:1px solid var(--line);font-size:13px">Workspace blueprint 1.14 · Static reference from application components. Controls are inactive; no AI results. See WORKSPACE_SPEC.md, ANALYTICS_SPEC.md and SKILLS_STUDIO_SPEC.md. Run the application for interactive review.</p>${markup}</body></html>`);
} finally {rmSync(dir,{recursive:true,force:true});}
