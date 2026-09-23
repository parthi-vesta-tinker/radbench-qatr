import {test, expect} from '@playwright/test';
// Explicit canned fixture: validates rendered phases and copy, not clinical performance.
test('F3 phases and copy survive completion and reload',async({page,request})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  const config=await (await request.get('/api/v1/config')).json();
  const sample=config.samples.find((s:{id:string})=>s.id==='mixed');
  await page.goto('/');
  await expect(page).toHaveTitle(/Vesta/);
  await page.getByLabel('Report text',{exact:true}).fill(sample.report_text);
  await page.getByRole('button',{name:'Review',exact:true}).click();
  await expect(page.getByText('AI review',{exact:true})).toBeVisible();
  await expect(page.getByText('Output',{exact:true})).toBeVisible();
  await expect(page.locator('.review-journey .complete')).toHaveCount(4);
  await expect(page.getByText('Language review',{exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'Copy all comments',exact:true}).click();
  const copied=await page.evaluate(()=>navigator.clipboard.readText());
  expect(copied).toContain('PACS comments:');
  expect(copied).not.toContain('QA review');
  expect(copied).toContain('Critical Findings comments:');
  expect(copied).not.toContain('missed flag');
  expect(copied).not.toMatch(/^\d+\. /m);
  await expect(page.getByText('Copied.',{exact:true})).toHaveCount(0);
  await expect(page.getByRole('heading',{name:'PACS comments',exact:true})).toBeVisible();
  await expect(page.locator('.comment-section ol')).toHaveCount(0);
  for (const name of ['Copy PACS comments','Copy critical']) {
    await page.getByRole('button',{name,exact:true}).click();
    const group=await page.evaluate(()=>navigator.clipboard.readText());
    expect(group).not.toContain('QA review');
    expect(group).not.toMatch(/^\d+\. /m);
    expect(group.startsWith(name==='Copy PACS comments' ? 'PACS comments:' : 'Critical Findings comments:')).toBe(true);
  }
  for (const width of [1536,390,320]) {
    await page.setViewportSize({width,height:900});
    const buttons=await page.locator('.copy-action').all();
    const bounds=await Promise.all(buttons.map(button=>button.boundingBox()));
    for(const box of bounds) {
      expect(Math.abs(box!.x-bounds[0]!.x)).toBeLessThan(2);
      expect(Math.abs(box!.width-bounds[0]!.width)).toBeLessThan(2);
    }
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    await page.screenshot({path:`/tmp/qa-copy-alignment-${width}.png`,fullPage:true});
  }

  await page.reload();
  await expect(page.locator('.review-journey .complete')).toHaveCount(4);
  await page.screenshot({path:'/tmp/radbench-f3-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:'/tmp/radbench-f3-mobile.png',fullPage:true});
  expect(errors).toEqual([]);
});
