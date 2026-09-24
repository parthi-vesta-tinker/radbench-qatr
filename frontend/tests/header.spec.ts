import {test, expect} from '@playwright/test';

test('branded header, feature notice and icon actions remain usable at narrow widths', async ({page}) => {
  const errors:string[]=[];
  let probes=0;
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{if(request.url().endsWith('/diagnostics/openai'))probes++;});
  await page.goto('/');
  await expect(page.locator('.brand')).toHaveText('VestaRadiology Report Review');
  expect(await page.locator('.brand img').evaluate((image:HTMLImageElement)=>image.complete && image.naturalWidth>0)).toBe(true);
  for(const name of ['Share — coming soon']) {
    const button=page.getByRole('button',{name,exact:true});
    await expect(button).toHaveAttribute('aria-disabled','true');
    await button.hover();await expect(page.getByRole('tooltip',{name,exact:true})).toBeVisible();
    await button.focus();await button.press('Escape');
    await expect(page.getByRole('tooltip',{name,exact:true})).toBeHidden();
  }
  await expect(page.getByRole('button',{name:'Settings',exact:true})).toBeEnabled();
  const health=page.getByRole('button',{name:'Service health: Local checks passed',exact:true});
  await expect(health).toBeVisible();
  await health.click();await expect(page.getByRole('dialog',{name:'Service health',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Close service health'}).click();await expect(health).toBeFocused();
  const notice=page.getByLabel('New feature',{exact:true});
  await expect(notice).toHaveText('New: Collapsible panels');
  const noticeHeight=(await notice.boundingBox())!.height;
  expect(noticeHeight).toBeLessThan(50);
  await page.keyboard.press('Escape');
  await page.screenshot({path:'/tmp/radbench-header-desktop.png'});
  await page.getByRole('button',{name:'Switch to dark theme'}).click();
  await page.mouse.move(600,0);await page.keyboard.press('Escape');
  await page.screenshot({path:'/tmp/radbench-header-dark.png'});
  await page.getByRole('button',{name:'Dismiss feature notice',exact:true}).click();
  await expect(notice).toHaveCount(0);
  await page.reload();await expect(notice).toHaveCount(0);
  for(const width of [390,320]) {
    await page.setViewportSize({width,height:844});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    const header=await page.locator('.app-header').boundingBox();
    expect(header!.height).toBeLessThanOrEqual(120);
    for(const name of ['Share — coming soon'])await expect(page.getByRole('button',{name,exact:true})).toBeVisible();
    await health.click();
    const bounds=(await page.getByRole('dialog',{name:'Service health',exact:true}).boundingBox())!;
    expect(bounds.x).toBeGreaterThanOrEqual(0);expect(bounds.x+bounds.width).toBeLessThanOrEqual(width);
    await page.keyboard.press('Escape');
  }
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:'/tmp/radbench-header-mobile.png'});
  expect(probes).toBe(0);expect(errors).toEqual([]);
});
