import {test, expect} from '@playwright/test';

test('secondary sections remain readable and reachable at desktop and phone widths', async ({page}) => {
  await page.goto('/');
  for (const width of [1536, 390, 320]) {
    await page.setViewportSize({width, height:1024});
    for (const name of ['Review history', 'Feedbacks', 'Analytics', 'Skills', 'Playground']) {
      if (width <= 650) await page.getByRole('button', {name:'Open QA Studio', exact:true}).click();
      await page.mouse.move(0, 0);
      const tool = page.getByRole('button', {name, exact:true});
      await tool.focus();
      await tool.press('Enter');
      const main = page.locator('main.history-pane:visible');
      await expect(main.getByRole('heading', {name, exact:true, level:1})).toBeVisible();
      await expect(main.getByRole('status')).toHaveCount(0);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      for (const control of await main.locator('input:visible, select:visible, textarea:visible').all()) {
        const bounds = (await control.boundingBox())!;
        expect(bounds.x).toBeGreaterThanOrEqual(0);
        expect(bounds.x + bounds.width).toBeLessThanOrEqual(width);
      }
      if (width !== 320) await page.screenshot({path:`/tmp/qa-section-${name.replaceAll(' ', '-')}-${width}.png`,fullPage:true});
    }
  }
});
