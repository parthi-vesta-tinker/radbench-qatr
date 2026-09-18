import {test, expect} from '@playwright/test';
// Explicit canned fixture: validates rendered phases and copy, not clinical performance.
test('F3 phases and copy survive completion and reload',async({page,request})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  const config=await (await request.get('/api/v1/config')).json();
  const sample=config.samples.find((s:{id:string})=>s.id==='mixed');
  await page.goto('/');
  await expect(page).toHaveTitle(/Vesta/);
  await page.getByLabel('Report input',{exact:true}).fill(sample.report_text);
  await page.getByRole('button',{name:'Review report',exact:true}).click();
  await expect(page.getByText('Combined report review',{exact:true})).toBeVisible();
  await expect(page.getByText('Output validation',{exact:true})).toBeVisible();
  await expect(page.locator('.steps .completed')).toHaveCount(4);
  await expect(page.getByText('Language review',{exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'Copy all comments',exact:true}).click();
  const copied=await page.evaluate(()=>navigator.clipboard.readText());
  expect(copied).toContain('General Comments:');
  expect(copied).toContain('Critical Findings comments:');
  expect(copied).not.toContain('missed flag');
  await page.reload();
  await expect(page.locator('.steps .completed')).toHaveCount(4);
  await page.screenshot({path:'/tmp/radbench-f3-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:'/tmp/radbench-f3-mobile.png',fullPage:true});
  expect(errors).toEqual([]);
});
