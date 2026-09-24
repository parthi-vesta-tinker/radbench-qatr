import {test, expect} from '@playwright/test';

test('analytics counts saved findings and filters the selected period', async ({page,request}) => {
  const errors:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));
  const config=await (await request.get('/api/v1/config')).json();
  await page.goto('/');
  for (const id of ['mixed','discrepancy']) {
    const report=config.samples.find((sample:{id:string})=>sample.id===id).report_text;
    await page.getByRole('button',{name:'New review',exact:true}).click();
    await page.getByLabel('Report text',{exact:true}).fill(report);
    await page.getByRole('button',{name:'Review',exact:true}).click();
    await expect(page.locator('.review-journey .complete')).toHaveCount(4);
  }
  await page.getByRole('button',{name:'Analytics',exact:true}).click();
  const period=page.getByRole('combobox',{name:'Period',exact:true});
  await expect(period).toHaveValue('24h');
  await period.selectOption('1h');
  const findings=page.getByRole('region',{name:'Review findings'});
  await expect(findings.locator('dd')).toHaveText(['1','1','0','1']);
  await expect(page.getByRole('region',{name:'Review activity'}).locator('dd')).toHaveText(['2','2','0']);
  await expect(page.getByRole('combobox',{name:'Source'})).toHaveCount(0);
  await page.screenshot({path:'/tmp/qa-analytics-desktop.png'});
  await period.selectOption('7d');
  await expect(findings.locator('dd')).toHaveText(['1','1','0','1']);
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:'/tmp/qa-analytics-mobile.png'});
  await page.setViewportSize({width:320,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:'/tmp/qa-analytics-narrow.png'});
  expect(errors).toEqual([]);
});
