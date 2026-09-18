import { test, expect } from '@playwright/test';

test('component status shows actual local checks and never probes OpenAI automatically', async ({ page }) => {
  let probes = 0;
  page.on('request', request => { if (request.url().endsWith('/diagnostics/openai')) probes++; });
  await page.goto('/');
  await page.getByText('Health · Local checks passed', {exact:true}).click();
  for (const label of ['API backend', 'Database', 'DBOS', 'QA skills', 'OpenAI']) {
    await expect(page.locator('.system-status dt').filter({hasText:label})).toBeVisible();
  }
  await expect(page.getByRole('button', {name:'Check OpenAI connection'})).toBeDisabled();
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
