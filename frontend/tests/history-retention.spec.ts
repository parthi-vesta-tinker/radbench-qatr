import {test, expect} from '@playwright/test';

test('New review preserves earlier submissions in the sidebar and history after reload', async ({page,request}) => {
  const errors:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));
  const config=await (await request.get('/api/v1/config')).json();
  const reports=['mixed','clean'].map(id=>config.samples.find((sample:{id:string})=>sample.id===id).report_text);
  const ids:string[]=[];
  await page.goto('/');
  await expect(page).toHaveTitle(/Vesta/);
  for (const report of reports) {
    await page.getByRole('button',{name:'New review',exact:true}).click();
    await expect(page.getByRole('heading',{name:'New review',exact:true})).toBeVisible();
    await expect(page.getByLabel('Report text',{exact:true})).toHaveValue('');
    await page.getByLabel('Report text',{exact:true}).fill(report);
    const created=page.waitForResponse(response=>response.request().method()==='POST' && response.url().endsWith('/api/v1/reviews'));
    await page.getByRole('button',{name:'Review',exact:true}).click();
    ids.push((await (await created).json()).id);
    await expect(page.locator('.review-journey .complete')).toHaveCount(4);
  }
  expect(ids[0]).not.toBe(ids[1]);
  for (const id of ids) await expect(page.locator('.report-row').filter({hasText:id.slice(-5).toUpperCase()})).toBeVisible();
  await page.reload();
  await page.getByRole('button',{name:'Review history',exact:true}).click();
  for (let index=0;index<ids.length;index++) {
    const id=ids[index];
    await expect(page.getByRole('button',{name:id.slice(-5).toUpperCase(),exact:true})).toBeVisible();
    const saved=await (await request.get(`/api/v1/reviews/${id}`)).json();
    expect(saved.input.report_text).toBe(reports[index]);
    expect(saved.input_version).toBe(1);
  }
  await page.screenshot({path:'/tmp/qa-history-retention.png'});
  await page.getByRole('button',{name:ids[0].slice(-5).toUpperCase(),exact:true}).click();
  await expect(page.getByLabel('Report text',{exact:true})).toHaveValue(reports[0]);
  expect(errors).toEqual([]);
});
