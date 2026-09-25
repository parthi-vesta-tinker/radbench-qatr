import { test, expect } from '@playwright/test';

// UI fixtures only. No provider calls or clinical assertions.
for (const width of [1536, 390]) {
  test(`Classification inputs, breakdown and selected review at ${width}px`, async ({page, request}) => {
    await page.setViewportSize({width, height: 1000});
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    await page.route('**/api/v1/config', async route => {
      const response = await route.fetch();
      const config = await response.json();
      await route.fulfill({json: {...config, features: {...config.features, classification: true}}});
    });
    const labels = {finding_group: 'thoracic', certainty: 'definite', urgency: 'cannot_determine', polarity: 'affirmed', temporal_status: 'not_stated'};
    const fields = Object.fromEntries(Object.entries(labels).map(([field, label]) => [field, {label, raw_probabilities: {[label]: .9, other: .1}, provider_confidence: .85, top_probability: .9, margin: .8, review_reasons: []}]));
    const questions = Object.fromEntries(Object.keys(labels).map(field => [field, {type:'choice', instructions:`Saved question for ${field}.`, criteria: {[labels[field as keyof typeof labels]]: 'Saved criterion for this classification.', other: 'Alternative criterion.'}}]));
    await page.route('**/api/v1/classifications/config', route => route.fulfill({json: {enabled:true, ready:true, labels:Object.fromEntries(Object.entries(labels).map(([key,value]) => [key,[value]]))}}));
    let source: any;
    let status = 'running';
    await page.route(/\/api\/v1\/reviews\?/, async route => {
      const response = await route.fetch();
      const body = await response.json();
      await route.fulfill({json:{...body,items:body.items.map((item:any) => item.id === source?.id ? {...item,classification_overview:[{finding_group:'thoracic',communication_priority:'cannot_determine'}]} : item)}});
    });
    await page.route('**/api/v1/analytics?*', async route => {
      const response = await route.fetch();
      const body = await response.json();
      await route.fulfill({json:{...body,classification:{finding_groups:{thoracic:1},communication_priorities:{cannot_determine:1}}}});
    });
    let analysisReads = 0;
    let mutations = 0;
    await page.route('**/api/v1/reviews/*/classifications', async route => {
      const reviewId = route.request().url().split('/').at(-2);
      const classifiedSource = await (await request.get('/api/v1/reviews/'+reviewId)).json();
      return route.fulfill({json: classifiedSource.result ? [{
      id:'jc-browser',review_id:classifiedSource.id,input_version:classifiedSource.input_version,observation_id:classifiedSource.result.critical_comments[0].observation_id,
      input:{finding_text:'Acute right pneumothorax.', qa_comment:'Review the critical observation.', source:'report_excerpts'},
      source_status:'current',execution_status:status,steps:[{step_id:'jev_classification',status:status}],
      result: status === 'completed' ? {fields,calibration_status:'uncalibrated',duration_ms:120,usage:{input_tokens:50,output_tokens:20}} : null,
      provenance:{model:'jev-1.13.0',rubric_id:'saved-rubric'},created_at:new Date().toISOString(),updated_at:new Date().toISOString(),
    }] : []}); });
    await page.route('**/api/v1/classifications/jc-browser/analysis', route => {
      analysisReads++;
      return route.fulfill({json:{classification_id:'jc-browser',model:'jev-1.13.0',state: width === 1536 ? {target:{report_excerpts:[{section:'impression',text:'Acute right pneumothorax.'}]},report_context:'Findings: Acute right pneumothorax.\nImpression: Acute right pneumothorax.',qa_comment:'Review the critical observation.'} : {finding_text:'Acute right pneumothorax.',qa_comment:'Review the critical observation.',report_quotes:['Acute right pneumothorax.']},questions,rubric_id:'saved-rubric',rubric_version:'1.0.0',rubric_status:'draft_research',rubric_hash:'saved-hash'}});
    });
    page.on('request', request => { if(request.method() === 'POST' && request.url().includes('/classifications')) mutations++; });
    await page.goto('/');
    await expect(page).toHaveTitle(/Vesta/);
    async function tool(name: string) {
      if (width < 700) await page.getByRole('button',{name: name === 'New review' ? 'Open Report reviews' : 'Open QA Studio',exact:true}).click();
      await page.getByRole('button',{name,exact:true}).click();
    }
    await tool('Classification');
    await expect(page.locator('.classification-pane')).toContainText('Review this report to see classification.');
    await tool('New review');
    const config = await (await request.get('/api/v1/config')).json();
    await page.getByLabel('Report text',{exact:true}).fill(config.samples.find((item:any) => item.id === 'critical').report_text);
    const accepted = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/api/v1/reviews'));
    await page.getByRole('button',{name:'Review',exact:true}).click();
    const id = (await (await accepted).json()).id;
    await expect.poll(async () => { source = await (await request.get('/api/v1/reviews/'+id)).json(); return source.execution_status; }).toBe('completed');
    await expect(page.locator('.review-journey')).toContainText('Results');
    await expect(page.locator('.review-journey li').last()).toContainText('Classification');
    await expect(page.locator('.review-journey li').last()).toHaveClass('current');
    status = 'completed';
    await expect(page.locator('.review-journey li').last()).toHaveClass('complete');
    // Connector halves meet at each column boundary, even for the wider last stage.
    const connectors = await page.locator('.review-journey li').evaluateAll(items => items.slice(0,-1).map((item,index) => {
      const next = items[index+1];
      const right = getComputedStyle(item,'::after');
      const left = getComputedStyle(next,'::before');
      return {end:item.getBoundingClientRect().x + parseFloat(right.left) + parseFloat(right.width), start:next.getBoundingClientRect().x + parseFloat(left.left), rightY:right.top, leftY:left.top};
    }));
    for (const line of connectors) { expect(Math.abs(line.end-line.start)).toBeLessThan(1); expect(line.rightY).toBe(line.leftY); }
    await page.screenshot({path:`/tmp/qa-classification-journey-${width}.png`,fullPage:true});
    if (width < 700) await page.getByRole('button',{name:'Open QA Studio',exact:true}).click();
    const guidance = page.locator('section[aria-label="Post-review Guidance"]');
    await expect(guidance.locator('.guidance li:visible')).toHaveCount(2);
    await guidance.getByRole('button',{name:'3 more steps',exact:true}).click();
    await expect(guidance.locator('.guidance li:visible')).toHaveCount(5);
    await guidance.getByRole('button',{name:'Post-review Guidance',exact:true}).click();
    await expect(guidance.locator('.guidance li:visible')).toHaveCount(2);
    await guidance.getByRole('button',{name:'Post-review Guidance',exact:true}).click();
    await expect(guidance.locator('.guidance li:visible')).toHaveCount(5);
    await guidance.getByRole('button',{name:'Post-review Guidance',exact:true}).click();
    const overview = page.locator('section[aria-label="Classification Overview"]');
    await expect(overview.locator('.classification-priority')).toHaveText('PriorityCannot determine');
    await expect(overview.locator('.classification-group')).toHaveCSS('font-weight','500');
    await page.screenshot({path:`/tmp/qa-studio-preview-${width}.png`,fullPage:true});
    await overview.getByRole('button',{name:'More details',exact:true}).click();
    await expect(overview.locator('.jev-labels')).toContainText('Report certainty');
    await expect(overview.locator('.jev-labels')).toContainText('Polarity');
    await expect(overview.locator('.jev-labels')).toContainText('Temporal status');
    await expect(overview.getByRole('button',{name:'Something wrong?',exact:true})).toBeVisible();
    await page.screenshot({path:`/tmp/qa-studio-expanded-${width}.png`,fullPage:true});
    if (width < 700) await page.getByRole('button',{name:'Close QA Studio',exact:true}).click();
    await tool('Classification');
    const pane = page.locator('.classification-pane');
    await expect(pane).toContainText('Thoracic');
    await expect(pane.locator('.jev-inputs')).not.toHaveAttribute('open','');
    await pane.getByText('Inputs used',{exact:true}).click();
    await expect(pane.locator('.jev-inputs')).toContainText('Report excerpts + QA comment');
    await expect(pane.locator('.jev-finding').first()).toBeVisible();
    await pane.getByText('State · Inputs sent to JEV',{exact:true}).click();
    await expect(pane.locator('.classification-state')).toContainText('Acute right pneumothorax.');
    if (width === 1536) await expect(pane.locator('.classification-state')).toContainText('Report context');
    else await expect(pane.locator('.classification-state')).toContainText('Report quotes');
    await pane.getByText('Question and criteria',{exact:true}).first().click();
    await expect(pane).toContainText('Saved question for finding_group.');
    await expect(pane).toContainText('Saved criterion for this classification.');
    await pane.getByText('Run details',{exact:true}).click();
    await expect(pane).toContainText('saved-rubric · 1.0.0');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({path:`/tmp/qa-classification-${width}.png`,fullPage:true});
    await page.getByRole('button',{name:'Switch to dark theme'}).click();
    await page.screenshot({path:`/tmp/qa-classification-dark-${width}.png`,fullPage:true});
    await tool('New review');
    await tool('Classification');
    await expect(pane).toContainText('Review this report to see classification.');
    await expect(pane).not.toContainText('Thoracic');
    await tool('Review history');
    const classificationCell = page.locator('tr').filter({has:page.getByRole('button',{name:source.id.slice(-5).toUpperCase(),exact:true})}).locator('td[data-label="Classification"]');
    await expect(classificationCell).toContainText('Thoracic');
    await expect(classificationCell).toContainText('Priority: Cannot determine');
    await expect(classificationCell).not.toContainText('Definite');
    await expect(classificationCell).not.toContainText('Affirmed');
    await page.screenshot({path:`/tmp/qa-history-classification-${width}.png`,fullPage:true});
    await tool('Analytics');
    const counts = page.getByRole('region',{name:'Classification counts',exact:true});
    await expect(counts).toContainText('Thoracic');
    await expect(counts).toContainText('Cannot determine');
    await expect(counts.locator('dd')).toHaveText(['1','1']);
    await expect(counts).not.toContainText('Certainty');
    await expect(counts).not.toContainText('Polarity');
    await page.screenshot({path:`/tmp/qa-analytics-classification-${width}.png`,fullPage:true});
    expect(analysisReads).toBe(1);
    expect(mutations).toBe(0);
    expect(errors).toEqual([]);
    await expect(page.locator('vite-error-overlay')).toHaveCount(0);
  });
}

for (const width of [1536, 390]) {
  test(`No critical findings and Back to report preserve the selected report at ${width}px`, async ({page, request}) => {
    await page.setViewportSize({width, height:1000});
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if(message.type() === 'error') errors.push(message.text()); });
    await page.route('**/api/v1/config', async route => {
      const response = await route.fetch();
      const config = await response.json();
      await route.fulfill({json:{...config,features:{...config.features,classification:true}}});
    });
    await page.goto('/');
    await expect(page).toHaveTitle(/Vesta/);
    const draftText = 'Findings: Unsubmitted work. Impression: Preserve this draft.';
    await page.getByLabel('Report text',{exact:true}).fill(draftText);
    const config = await (await request.get('/api/v1/config')).json();
    const reportText = config.samples.find((sample:any) => sample.id === 'clean').report_text;
    const accepted = await request.post('/api/v1/reviews', {data:{report_text:reportText}, headers:{'Idempotency-Key':crypto.randomUUID()}});
    expect(accepted.status()).toBe(202);
    const id = (await accepted.json()).id;
    await expect.poll(async () => (await (await request.get('/api/v1/reviews/'+id)).json()).execution_status).toBe('completed');
    await page.getByRole('button',{name:'Refresh current data',exact:true}).click();
    if (width < 700) await page.getByRole('button',{name:'Open Report reviews',exact:true}).click();
    await page.locator('.report-row').filter({has:page.locator('.rail-id',{hasText:id.slice(-5).toUpperCase()})}).click();
    await expect(page.getByLabel('Report text',{exact:true})).toHaveValue(reportText);
    const stage = page.locator('.review-journey li').last();
    await expect(stage).toHaveClass('not-applicable');
    await expect(stage).toContainText('not applicable — no critical findings reported');
    await expect(stage.locator('.lucide-minus')).toBeVisible();
    await page.screenshot({path:`/tmp/qa-classification-not-applicable-${width}.png`,fullPage:true});
    if (width < 700) await page.getByRole('button',{name:'Open QA Studio',exact:true}).click();
    await page.getByRole('button',{name:'Classification',exact:true}).click();
    const pane = page.locator('.classification-pane');
    await expect(pane).toContainText('No critical findings were reported. Classification is not applicable.');
    await expect(pane).not.toContainText('No classification available.');
    await page.screenshot({path:`/tmp/qa-classification-empty-${width}.png`,fullPage:true});
    await page.getByRole('button',{name:'Back to report',exact:true}).click();
    await expect(page.getByRole('heading',{name:'Report review',exact:true})).toBeVisible();
    await expect(page.getByLabel('Report text',{exact:true})).toHaveValue(reportText);
    if (width < 700) await page.getByRole('button',{name:'Open Report reviews',exact:true}).click();
    await page.getByRole('button',{name:'Current review',exact:true}).click();
    await expect(page.getByLabel('Report text',{exact:true})).toHaveValue(draftText);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await expect(page.locator('vite-error-overlay')).toHaveCount(0);
    expect(errors).toEqual([]);
  });
}
