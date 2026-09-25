import {test,expect} from '@playwright/test';

test('settings save model and feature choices, persist across reload, and enforce backend gates',async({page,request})=>{
 const initial=await (await request.get('/api/v1/settings')).json();
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 try {
  await page.goto('/');await expect(page).toHaveTitle(/Vesta/);
  await page.getByLabel('Report text',{exact:true}).fill('Unsubmitted report stays here.');
  await page.getByRole('button',{name:'Settings',exact:true}).click();
  const panel=page.getByRole('dialog',{name:'Settings',exact:true});
  await expect(panel).toBeVisible();
  await expect(panel.getByRole('button',{name:'Save',exact:true})).toHaveCount(0);
  await expect(panel.getByRole('button',{name:'Close',exact:true})).toBeVisible();
  await expect(panel.getByLabel('Run mode',{exact:true})).toHaveValue('demo');
  await expect(panel.getByText('Local',{exact:true})).toBeVisible();
  await panel.getByLabel('Clinical review model',{exact:true}).selectOption('controlled-second-model');
  await expect(panel.getByRole('button',{name:'Save',exact:true})).toBeVisible();
  await expect(panel.getByRole('button',{name:'Close',exact:true})).toHaveCount(0);
  await panel.getByLabel('Clinical review model',{exact:true}).selectOption(initial.core_model);
  await expect(panel.getByRole('button',{name:'Save',exact:true})).toHaveCount(0);
  await expect(panel.getByRole('button',{name:'Close',exact:true})).toBeVisible();
  await panel.getByLabel('Clinical review model',{exact:true}).selectOption('controlled-second-model');
  await panel.getByRole('switch',{name:'Playground',exact:true}).uncheck();
  await panel.getByRole('switch',{name:'Skills',exact:true}).uncheck();
  await panel.getByRole('button',{name:'Save',exact:true}).click();
  await expect(panel).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Settings',exact:true})).toBeFocused();
  await expect(page.getByLabel('Report text',{exact:true})).toHaveValue('Unsubmitted report stays here.');
  await expect(page.getByRole('button',{name:'Playground',exact:true})).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Skills',exact:true})).toHaveCount(0);
  expect((await request.get('/api/v1/playground')).status()).toBe(403);
  expect((await request.get('/api/v1/knowledge')).status()).toBe(403);
  const config=await (await request.get('/api/v1/config')).json();
  expect(config.model).toBe('controlled-second-model');expect(config.run_mode).toBe('demo');
  await page.reload();
  await expect(page.getByRole('button',{name:'Playground',exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'Settings',exact:true}).click();
  await expect(panel.getByLabel('Clinical review model',{exact:true})).toHaveValue('controlled-second-model');
  for(const width of [1536,390,320]){
   await page.setViewportSize({width,height:900});
   const box=(await panel.boundingBox())!;expect(box.x).toBeGreaterThanOrEqual(0);expect(box.x+box.width).toBeLessThanOrEqual(width);
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
   await page.screenshot({path:`/tmp/qa-settings-${width}.png`});
  }
  await page.keyboard.press('Escape');await expect(panel).toHaveCount(0);
  await page.getByRole('button',{name:'Settings',exact:true}).click();
  await panel.getByRole('switch',{name:'Playground',exact:true}).check();
  await panel.getByRole('switch',{name:'Skills',exact:true}).check();
  await panel.getByRole('button',{name:'Save',exact:true}).click();
  await expect(panel).toHaveCount(0);
  expect(errors).toEqual([]);
 }finally {
  const current=await (await request.get('/api/v1/settings')).json();
  const result=await request.put('/api/v1/settings',{data:{revision:current.revision,run_mode:initial.run_mode,core_model:initial.core_model,features:initial.features}});
  expect(result.status()).toBe(200);
 }
});

test('settings handles missing provider configuration and concurrent edits',async({page,request})=>{
 await page.goto('/');await page.getByRole('button',{name:'Settings',exact:true}).click();
 const panel=page.getByRole('dialog',{name:'Settings',exact:true});
 await panel.getByLabel('Run mode',{exact:true}).selectOption('live');
 await panel.getByRole('button',{name:'Save',exact:true}).click();
 await expect(panel.getByRole('alert')).toContainText('OPENAI_API_KEY');
 await panel.getByRole('button',{name:'Reload settings'}).click();
 await expect(panel.getByLabel('Run mode',{exact:true})).toHaveValue('demo');
 const current=await (await request.get('/api/v1/settings')).json();
 await request.put('/api/v1/settings',{data:{revision:current.revision,run_mode:current.run_mode,core_model:current.core_model,features:current.features}});
 await panel.getByRole('switch',{name:'Skills',exact:true}).uncheck();
 await panel.getByRole('button',{name:'Save',exact:true}).click();
 await expect(panel.getByRole('alert')).toContainText('changed elsewhere');
 await expect(panel.getByRole('switch',{name:'Skills',exact:true})).not.toBeChecked();
});

test('full-screen Classification is opt-in and hiding it returns to the report', async({page,request})=>{
 const initial=await (await request.get('/api/v1/settings')).json();
 const config=await (await request.get('/api/v1/config')).json();
 let saved={...initial,classification_configured:true,features:{...initial.features,classification:true,classification_analysis:false}};
 await page.route('**/api/v1/settings',async route=>{
  if(route.request().method()==='PUT') saved={...saved,...route.request().postDataJSON(),revision:saved.revision+1};
  await route.fulfill({json:saved});
 });
 await page.route('**/api/v1/config',async route=>{
  await route.fulfill({json:{...config,features:saved.features}});
 });
 await page.goto('/');
 await page.getByLabel('Report text',{exact:true}).fill('Preserve this unfinished report.');
 const tool=page.locator('#studio-panel').getByRole('button',{name:'Classification',exact:true});
 await expect(tool).toHaveCount(0);
 await page.getByRole('button',{name:'Settings',exact:true}).click();
 let panel=page.getByRole('dialog',{name:'Settings',exact:true});
 await expect(panel.getByRole('switch',{name:'Classification Overview',exact:true})).toBeChecked();
 await expect(panel.getByRole('switch',{name:'Classification analysis',exact:true})).not.toBeChecked();
 await page.screenshot({path:'/tmp/qa-analysis-setting-default.png'});
 await panel.getByRole('switch',{name:'Classification analysis',exact:true}).check();
 await panel.getByRole('button',{name:'Save',exact:true}).click();
 await tool.click();await expect(page.locator('.classification-pane')).toBeVisible();
 await page.getByRole('button',{name:'Settings',exact:true}).click();
 panel=page.getByRole('dialog',{name:'Settings',exact:true});
 await panel.getByRole('switch',{name:'Classification analysis',exact:true}).uncheck();
 await panel.getByRole('button',{name:'Save',exact:true}).click();
 await expect(tool).toHaveCount(0);
 await expect(page.locator('.classification-pane')).toHaveCount(0);
 await expect(page.getByLabel('Report text',{exact:true})).toHaveValue('Preserve this unfinished report.');
 expect(saved.features.classification).toBe(true);
 await page.reload();
 await expect(page.locator('.review-journey')).toContainText('Classification');
 await expect(tool).toHaveCount(0);
 await page.unrouteAll({behavior:'wait'});
});
