import {test, expect} from '@playwright/test';
// These checks verify UI state only. No clinical completion or AI outcome is fabricated.
test('drafts, Undo, Studio navigation and themes remain usable on desktop and mobile',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');await expect(page).toHaveTitle(/Vesta/);
  await expect(page.getByRole('heading',{name:'QA Studio'})).toBeVisible();
  await expect(page.getByRole('group',{name:'Execution mode for new reviews'})).toHaveCount(0);
  await expect(page.getByLabel('Load synthetic example')).toHaveCount(0);
  await page.getByLabel('Report text',{exact:true}).fill('First draft');
  await page.getByRole('button',{name:'New report',exact:true}).click();
  await page.getByLabel('Report text',{exact:true}).fill('Second draft');
  await page.getByRole('button',{name:'Delete draft 1',exact:true}).click();
  await expect(page.getByLabel('Report text',{exact:true})).toHaveValue('Second draft');
  await page.getByRole('button',{name:'Undo',exact:true}).click();
  await expect(page.getByLabel('Report text',{exact:true})).toHaveValue('First draft');
  for(const tool of ['Review history','Feedbacks','Analytics','Skills & knowledge']){
    await page.getByRole('button',{name:tool,exact:true}).click();
    await expect(page.locator('.history-pane:visible h1')).toHaveText(tool);
    await page.getByRole('button',{name:'Current report',exact:true}).click();
    await expect(page.getByLabel('Report text',{exact:true})).toHaveValue('First draft');
  }
  await page.getByRole('button',{name:'Switch to dark theme'}).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme','dark');
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.getByRole('button',{name:'Switch to light theme'}).click();
  await page.locator('.system-status summary').dblclick();
  await expect(page.getByRole('heading',{name:'Service health'})).toBeVisible();
  await page.locator('.system-status summary').press('Escape');
  await expect(page.getByRole('heading',{name:'Service health'})).toBeHidden();
  expect(errors).toEqual([]);
});

test('Skills Studio compares and saves editorial revisions without activating them',async({page})=>{
  await page.goto('/');
  await page.getByRole('button',{name:'Skills & knowledge',exact:true}).click();
  await expect(page.getByRole('textbox',{name:'Draft content',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Compare with installed',exact:true}).click();
  const installed=await page.getByRole('textbox',{name:'Installed content',exact:true}).inputValue();
  await page.getByRole('textbox',{name:'Draft content',exact:true}).fill(installed+'\nEditorial UI test note.\n');
  await page.getByLabel('Change summary',{exact:true}).fill('Verify draft storage only.');
  await page.getByRole('button',{name:'Save draft',exact:true}).click();
  await expect(page.getByText(/Draft revision .* saved. Installed instructions remain active./)).toBeVisible();
  await expect(page.getByRole('textbox',{name:'Installed content',exact:true})).toHaveValue(installed);
  await page.getByRole('button',{name:'Current report',exact:true}).click();
  await page.getByRole('button',{name:'Skills & knowledge',exact:true}).click();
  await expect(page.getByRole('textbox',{name:'Draft content',exact:true})).toHaveValue(installed+'\nEditorial UI test note.\n');
});

test('real API input validation keeps the submitted report editable for another review',async({page})=>{
  await page.goto('/');
  // Invalid input exercises the actual API/DBOS parser and stops before any model stage.
  await page.getByLabel('Report text',{exact:true}).fill('Only a preamble, no required sections.');
  await page.getByRole('button',{name:'Review',exact:true}).click();
  await expect(page.getByRole('heading',{name:'More information needed'})).toBeVisible();
  // The accepted report stays editable; Review again only unlocks once the text changes.
  await expect(page.getByLabel('Report text',{exact:true})).toBeEditable();
  await expect(page.getByRole('button',{name:'Review again',exact:true})).toBeDisabled();
  await page.getByLabel('Report text',{exact:true}).fill('Findings:\nLungs are clear.\n\nImpression:\nNo acute abnormality.');
  await expect(page.getByRole('button',{name:'Review again',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'New report',exact:true}).click();
  await page.getByLabel('Report text',{exact:true}).fill('Another draft');
  await expect(page.getByLabel('Report text',{exact:true})).toBeEditable();
});

test('Studio analytics and inbox work without provider inference',async({page})=>{
  await page.goto('/');
  await page.getByRole('button',{name:'Analytics',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Are stakeholders accepting the work?'})).toBeVisible();
  await expect(page.locator('.measurement-grid strong')).toHaveText(['Not measured','Not measured','Not measured','Not measured']);
  await page.getByRole('combobox',{name:'Period',exact:true}).selectOption('all');
  await expect(page.getByRole('region',{name:'Feedback totals'})).toBeVisible();
  await page.getByRole('button',{name:'Feedbacks',exact:true}).click();
  await expect(page.getByRole('heading',{name:'No feedback matches these filters'})).toBeVisible();
  await page.getByRole('combobox',{name:'Rating',exact:true}).selectOption('');
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('feedback dialog is dismissable by Escape and Cancel, and reopens cleanly',async({page})=>{
  await page.goto('/');
  // A demo sample produces a completed result without any provider call.
  await page.getByLabel('Report text',{exact:true}).fill('Findings:\nLungs are clear. No pleural effusion or pneumothorax.\n\nImpression:\nNo acute cardiopulmonary abnormality.');
  await page.getByRole('button',{name:'Review',exact:true}).click();
  const dialog=page.getByRole('dialog');
  const heading=page.getByRole('heading',{name:'What should we improve?'});
  await page.getByRole('button',{name:'Thumbs down',exact:true}).click();
  await expect(heading).toBeVisible();
  await expect(page.getByRole('button',{name:'Save',exact:true})).toBeVisible();
  // Escape closes the native dialog without a React synthetic close event.
  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
  // A single click must reopen it: state and the element cannot drift apart.
  await page.getByRole('button',{name:'Thumbs down',exact:true}).click();
  await expect(heading).toBeVisible();
  await page.getByRole('button',{name:'Cancel',exact:true}).click();
  await expect(dialog).toBeHidden();
  await page.getByRole('button',{name:'Thumbs down',exact:true}).click();
  await expect(heading).toBeVisible();
});
