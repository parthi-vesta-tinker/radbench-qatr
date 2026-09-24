import { test, expect } from '@playwright/test';

test('component status shows actual local checks and never probes OpenAI automatically', async ({ page }) => {
  let probes = 0;
  page.on('request', request => { if (request.url().endsWith('/diagnostics/openai')) probes++; });
  await page.goto('/');
  await page.getByRole('button', {name:'Application health: Local checks passed',exact:true}).click();
  await expect(page.getByRole('heading', {name:'Application health'})).toBeVisible();
  // Healthy checks collapse behind a verdict; the full list stays one click away.
  await expect(page.getByText(/All 5 checks passed/)).toBeVisible();
  await page.getByText(/View all 5 checks/).click();
  for (const label of ['API backend', 'Database', 'DBOS', 'QA skills', 'OpenAI']) {
    await expect(page.locator('.system-status dt').filter({hasText:label})).toBeVisible();
  }
  await expect(page.getByRole('button', {name:'Check OpenAI connection'})).toBeDisabled();
  await expect(page.locator('.health-check-row').filter({hasText:'OpenAI'})).toContainText('Not configured');
  expect(probes).toBe(0);
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
});

test('configuration failure retains actionable code and retry recovers', async ({page}) => {
  await page.route('**/api/v1/config', route => route.fulfill({status:503, contentType:'application/json', headers:{'Request-Id':'req_windows_test'}, body:JSON.stringify({error:{code:'SKILL_INVENTORY_MISMATCH', message:'The skill package inventory does not match. Restore the updated Windows-compatible bundle.'}})}));
  await page.goto('/');
  await expect(page.getByText(/SKILL_INVENTORY_MISMATCH/)).toBeVisible();
  await expect(page.getByText(/req_windows_test/)).toBeVisible();
  await page.unroute('**/api/v1/config');
  await page.getByRole('button',{name:'Retry connection'}).click();
  await expect(page.getByText(/SKILL_INVENTORY_MISMATCH/)).toHaveCount(0);
});

test('HTML served at API URL is identified instead of called a backend outage', async ({page}) => {
  await page.route('**/api/v1/config', route => route.fulfill({contentType:'text/html',body:'<html>wrong server</html>'}));
  await page.goto('/');
  await expect(page.getByText(/INVALID_API_RESPONSE/)).toBeVisible();
});


test('health refresh and inline OpenAI checks show concise results and recover from failure', async ({page}) => {
  let statusCalls = 0, probes = 0;
  const times = ['2026-09-22T16:00:00Z','2026-09-22T16:05:00Z'];
  await page.route('**/api/v1/status', route => {
    const checked_at = times[Math.min(statusCalls++,1)];
    return route.fulfill({json:{status:'ready',checked_at,readiness_scope:'Local prerequisites only',components:{
      api:{status:'ok',message:'API responds'},database:{status:'ok',message:'Database responds'},
      dbos:{status:'ok',message:'Workflow responds'},skills:{status:'ok',message:'Skills respond'},
      openai:{status:'configured',message:'Model configured'},
    }}});
  });
  await page.route('**/api/v1/diagnostics/openai', route => {
    probes++;
    return route.fulfill({json:probes === 1 ? {status:'error',message:'OpenAI rejected the API key.',code:'OPENAI_AUTHENTICATION_FAILED'} :
      {status:'accessible',message:'OpenAI authentication and model metadata access succeeded. Inference has not been tested.'}});
  });
  await page.goto('/');
  await page.getByRole('button',{name:'Application health: Local checks passed',exact:true}).click();
  const popup=page.getByRole('dialog',{name:'Application health',exact:true});
  await expect(popup.locator('time')).toHaveAttribute('datetime',times[0]);
  await expect(popup.getByRole('button',{name:'Check OpenAI connection',exact:true})).toBeHidden();
  const disclosure=popup.locator('summary');
  await disclosure.focus();await page.keyboard.press('Enter');
  const rows=popup.locator('.health-check-row');
  await expect(rows).toHaveCount(5);
  const iconEdges = await rows.locator('dd > :last-child').evaluateAll(nodes => nodes.map(node => node.getBoundingClientRect().right));
  expect(Math.max(...iconEdges)-Math.min(...iconEdges)).toBeLessThanOrEqual(1);
  await expect(popup.locator('.health-last-checked br')).toHaveCount(0);
  const openai=rows.filter({hasText:'OpenAI'});
  await expect(openai).toContainText('Configured');
  await expect(popup).not.toContainText('API responds');
  expect(probes).toBe(0);
  await openai.getByRole('button',{name:'Check OpenAI connection',exact:true}).click();
  await expect(openai).toContainText('Error');
  await expect(popup.locator('.health-verdict')).toHaveText('1 of 5 checks need attention');
  await expect(popup.locator('.health-probe-result')).toContainText('OPENAI_AUTHENTICATION_FAILED');
  await openai.getByRole('button',{name:'Check OpenAI connection',exact:true}).click();
  await expect(openai).toContainText('Accessible');
  await expect(popup).not.toContainText('metadata');
  expect(probes).toBe(2);
  await popup.getByRole('button',{name:'Refresh status',exact:true}).click();
  await expect(popup.locator('time')).toHaveAttribute('datetime',times[1]);
  await expect(openai).toContainText('Configured');
  await expect(popup.locator('.health-probe-result')).toHaveCount(0);
  expect(probes).toBe(2);
  for (const theme of ['light','dark']) {
    if(theme==='dark') {
      await page.keyboard.press('Escape');
      await page.getByRole('button',{name:'Switch to dark theme'}).click();
      await page.locator('.health-trigger').click();
    }
    for(const width of [1280,390,320]) {
      await page.setViewportSize({width,height:844});
      const bounds=(await popup.boundingBox())!;
      expect(bounds.x).toBeGreaterThanOrEqual(0);
      expect(bounds.x+bounds.width).toBeLessThanOrEqual(width);
      expect(await popup.evaluate(node=>node.scrollWidth<=node.clientWidth)).toBe(true);
      const verdictBox=(await popup.locator('.health-verdict').boundingBox())!;
      const checkedBox=(await popup.locator('.health-last-checked').boundingBox())!;
      expect(Math.abs(verdictBox.y-checkedBox.y)).toBeLessThanOrEqual(3);
      await page.mouse.move(0,800);
      await page.screenshot({path:`/tmp/qa-health-${theme}-${width}.png`});
    }
  }
});
