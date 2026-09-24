import {test, expect} from '@playwright/test';

test('correcting a review replaces its text and result without another draft or history entry', async ({page,request}) => {
  const config = await (await request.get('/api/v1/config')).json();
  await page.goto('/');
  const input = page.getByLabel('Report text',{exact:true});
  await expect(page.getByText('Report text only',{exact:true})).toHaveCount(0);
  await input.fill('Findings: only findings.');
  const created = page.waitForResponse(r=>r.request().method()==='POST' && r.url().endsWith('/api/v1/reviews'));
  await page.getByRole('button',{name:'Review',exact:true}).click();
  const first = await (await created).json();
  await expect(page.locator('.review-journey .blocked')).toBeVisible();
  await expect(page.locator('.review-journey .blocked')).toContainText('Validate');
  await expect(page.locator('.review-journey #input-help[role="alert"]')).toBeVisible();
  await page.setViewportSize({width:390,height:900});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:'/tmp/qa-review-validation-error-390.png'});
  await page.setViewportSize({width:1536,height:1024});
  await input.fill(config.samples.find((s:{id:string})=>s.id==='mixed').report_text);
  await expect(page.locator('#input-help')).toContainText('Review again. Changes not reviewed');
  await expect(page.locator('#input-help button')).toHaveText('Restore change');
  for (const width of [390,320]) {
    await page.setViewportSize({width,height:900});
    const message = (await page.locator('#input-help').boundingBox())!;
    const restore = (await page.locator('#input-help button').boundingBox())!;
    expect(Math.abs(message.y-restore.y)).toBeLessThan(2);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  }
  await page.setViewportSize({width:1536,height:1024});
  const replaced = page.waitForResponse(r=>r.request().method()==='PUT' && r.url().endsWith('/reviews/'+first.id));
  await page.getByRole('button',{name:'Review again',exact:true}).click();
  expect((await (await replaced).json()).id).toBe(first.id);
  await expect(page.locator('.review-journey .complete')).toHaveCount(4);
  await expect(page.locator('.draft-row')).toHaveCount(0);
  await page.getByRole('button',{name:'Thumbs up',exact:true}).click();
  await expect(page.getByText('Feedback saved.',{exact:true})).toBeVisible();
  await input.fill(config.samples.find((s:{id:string})=>s.id==='clean').report_text);
  await expect(page.getByRole('button',{name:'Copy all comments',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'Review again',exact:true}).click();
  await expect(page.getByRole('heading',{name:'No actionable observations',exact:true})).toBeVisible();
  await expect(page.locator('.empty.clean svg')).toHaveCount(0);
  await expect(page.getByText('In the supplied report.',{exact:true})).toHaveCount(0);
  await expect(page.locator('.outcome-log')).toHaveCount(0);
  const feedback = await (await request.get(`/api/v1/reviews/${first.id}/feedback`)).json();
  expect(feedback.items).toHaveLength(1);
  expect(feedback.items[0]).not.toHaveProperty('result_version');
  const history = await (await request.get(`/api/v1/reviews?q=${first.id}`)).json();
  expect(history.items).toHaveLength(1);
  expect(history.items[0].status ?? history.items[0].execution_status).toBe('completed');
  for (const width of [1536,390,320]) {
    await page.setViewportSize({width,height:900});
    await expect(page.getByRole('navigation',{name:'Review progress'})).toBeVisible();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    const journey = (await page.locator('.review-journey').boundingBox())!;
    const button = (await page.getByRole('button',{name:'Review again',exact:true}).boundingBox())!;
    expect(Math.abs(journey.y-button.y)).toBeLessThan(2);
    expect(journey.x+journey.width).toBeLessThanOrEqual(button.x);
    await expect(page.locator('.review-journey li')).toHaveCount(4);
    await expect(page.locator('#input-help')).toHaveCount(1);
    const context = (await page.locator('#input-help').boundingBox())!;
    expect(context.y).toBeGreaterThan(journey.y);
    expect(context.x).toBeGreaterThanOrEqual(journey.x);
    expect(context.x+context.width).toBeLessThanOrEqual(journey.x+journey.width);
    await page.mouse.move(0,0);
    await page.screenshot({path:`/tmp/qa-review-journey-${width}.png`});
  }
});

test('skill configuration error is anchored to AI review', async ({page}) => {
  await page.route('**/api/v1/config', route => route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{code:'SKILL_CONFIGURATION_INVALID',message:'The skill package or configuration is invalid.'}})}));
  await page.setViewportSize({width:390,height:900});
  await page.goto('/');
  const stage = page.locator('.review-journey li[aria-describedby="input-help"]');
  await expect(stage).toContainText('AI review');
  await expect(stage).toHaveClass('blocked');
  await expect(page.locator('.review-journey .current')).toHaveCount(0);
  await expect(page.locator('.review-journey #input-help[role="alert"]')).toContainText('The skill package or configuration is invalid.');
  await expect(page.locator('#input-help')).not.toContainText('SKILL_CONFIGURATION_INVALID');
  await expect(page.locator('#input-help details')).toHaveCount(0);
  await expect(page.locator('#input-help button')).toHaveText('Retry connection');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:'/tmp/qa-review-config-error-390.png'});
});
