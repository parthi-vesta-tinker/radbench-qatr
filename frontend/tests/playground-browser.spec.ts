import {test,expect} from '@playwright/test';

test('sample browser filters use cases, previews reports, and preserves pasted text',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await expect(page).toHaveTitle(/Vesta/);
 await page.getByRole('button',{name:'Playground',exact:true}).click();
 const pane=page.locator('.playground-pane');
 await expect(pane.locator('.playground-sample')).toHaveCount(6);
 await expect(pane.locator('.playground-sample[aria-pressed="true"]')).toHaveCount(1);
 await expect(pane.getByRole('heading',{name:'Documented critical flag',exact:true})).toBeVisible();
 await expect(pane.getByRole('button',{name:'Run test review',exact:true})).toBeEnabled();
 await expect(pane.locator('.playground-banner')).toHaveCount(0);
 await expect(pane.locator('#playground-report')).toHaveCount(0);
 await pane.getByRole('combobox',{name:'Use case',exact:true}).selectOption('inconsistency');
 await expect(pane.locator('.playground-sample')).toHaveCount(3);
 await pane.getByRole('searchbox',{name:'Search samples'}).fill('laterality');
 await expect(pane.locator('.playground-sample')).toHaveCount(1);
 await pane.locator('.playground-sample').click();
 await expect(pane.getByRole('heading',{name:'Laterality mismatch',exact:true})).toBeVisible();
 const sampleText=await pane.locator('.playground-report-text').innerText();
 await pane.getByRole('searchbox',{name:'Search samples'}).fill('no-such-sample');
 await expect(pane.getByText('No matching samples.',{exact:true})).toBeVisible();
 await pane.getByRole('button',{name:'Clear filters'}).click();
 await expect(pane.locator('.playground-sample')).toHaveCount(6);
 await pane.getByRole('button',{name:/Uncertain critical concern/}).click();
 await expect(pane.getByRole('button',{name:'Run test review'})).toBeDisabled();
 await expect(pane.getByText(/This sample needs a configured model/)).toBeVisible();
 await pane.getByRole('button',{name:/Laterality mismatch/}).click();
 await pane.getByRole('button',{name:'Paste report',exact:true}).click();
 await pane.getByLabel('Report text',{exact:true}).fill('Findings: Preserved text. Impression: Preserved text.');
 await pane.getByRole('button',{name:'Sample reports',exact:true}).click();
 await expect(pane.locator('.playground-report-text')).toHaveText(sampleText);
 await pane.getByRole('button',{name:'Paste report',exact:true}).click();
 await expect(pane.getByLabel('Report text',{exact:true})).toHaveValue('Findings: Preserved text. Impression: Preserved text.');
 await page.getByRole('button',{name:'Review history',exact:true}).click();
 await page.getByRole('button',{name:'Playground',exact:true}).click();
 await expect(pane.getByLabel('Report text',{exact:true})).toHaveValue('Findings: Preserved text. Impression: Preserved text.');
 await pane.getByRole('button',{name:'Sample reports',exact:true}).click();
 for(const width of [1536,900,390,320]){
  await page.setViewportSize({width,height:1024});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await expect(pane.locator('.playground-report-text')).toHaveText(sampleText);
  for(const field of await pane.locator('input,select').all()){
   const box=(await field.boundingBox())!;expect(box.x).toBeGreaterThanOrEqual(0);expect(box.x+box.width).toBeLessThanOrEqual(width);
  }
  await pane.screenshot({path:`/tmp/qa-playground-after-${width}.png`});
 }
 await page.setViewportSize({width:1536,height:1024});
 await page.getByRole('button',{name:'Switch to dark theme'}).click();
 await pane.screenshot({path:'/tmp/qa-playground-after-dark.png'});
 expect(errors).toEqual([]);
});
