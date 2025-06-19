import { test, expect } from '@playwright/test';

test.describe('Comprehensive Dashboard Testing', () => {
  test('test all dashboard functionality comprehensively', async ({ page }) => {
    console.log('🔍 Running comprehensive dashboard test...');
    
    const errors: string[] = [];
    let apiCallsSuccess = 0;
    let apiCallsFailed = 0;
    
    // Monitor console errors and API calls
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
        console.log(`❌ Console Error: ${msg.text()}`);
      }
    });
    
    page.on('response', response => {
      const url = response.url();
      if (url.includes('6969')) {
        if (response.status() >= 200 && response.status() < 300) {
          apiCallsSuccess++;
          console.log(`✅ API Success: ${response.status()} ${url}`);
        } else {
          apiCallsFailed++;
          console.log(`❌ API Failed: ${response.status()} ${url}`);
        }
      }
    });
    
    // Test 1: Homepage
    console.log('\\n📍 Testing Homepage...');
    await page.goto('http://localhost:3001');
    await page.waitForTimeout(3000);
    
    const title = await page.title();
    console.log(`Title: ${title}`);
    expect(title).toBe('Headless PM Dashboard');
    
    // Check if data is loading
    const totalTasksElement = await page.locator('text=Total Tasks').first();
    await expect(totalTasksElement).toBeVisible();
    
    const taskCountElement = totalTasksElement.locator('..').locator('div').first();
    const taskCount = await taskCountElement.textContent();
    console.log(`Task count shows: ${taskCount}`);
    
    // Test 2: Navigation to Tasks page
    console.log('\\n📍 Testing Tasks Page...');
    await page.click('text=Tasks');
    await page.waitForTimeout(2000);
    
    await expect(page.locator('h1')).toContainText('Task Management');
    
    // Check Kanban board
    const taskColumns = await page.locator('.flex.gap-4').locator('> div').count();
    console.log(`Task columns: ${taskColumns}`);
    expect(taskColumns).toBeGreaterThan(0);
    
    // Test view switching
    await page.click('button:has-text("Analytics")');
    await page.waitForTimeout(1000);
    const analyticsVisible = await page.locator('text=Total Tasks').isVisible();
    console.log(`Analytics view working: ${analyticsVisible}`);
    expect(analyticsVisible).toBe(true);
    
    // Test 3: Agents page
    console.log('\\n📍 Testing Agents Page...');
    await page.goto('http://localhost:3001/agents');
    await page.waitForTimeout(2000);
    
    await expect(page.locator('h1')).toContainText('Agent Activity');
    const agentCards = await page.locator('.grid').locator('> div').count();
    console.log(`Agent cards: ${agentCards}`);
    
    // Test 4: Analytics page  
    console.log('\\n📍 Testing Analytics Page...');
    await page.goto('http://localhost:3001/analytics');
    await page.waitForTimeout(2000);
    
    await expect(page.locator('h1')).toContainText('Analytics');
    
    // Test 5: Communications page
    console.log('\\n📍 Testing Communications Page...');
    await page.goto('http://localhost:3001/communications');
    await page.waitForTimeout(2000);
    
    await expect(page.locator('h1')).toContainText('Communications');
    
    // Test 6: System Health page
    console.log('\\n📍 Testing System Health Page...');
    await page.goto('http://localhost:3001/health');
    await page.waitForTimeout(2000);
    
    await expect(page.locator('h1')).toContainText('System Health');
    
    // Take final screenshot
    await page.screenshot({ path: 'tests/screenshots/comprehensive-test.png', fullPage: true });
    
    // Final summary
    console.log('\\n📊 COMPREHENSIVE TEST SUMMARY:');
    console.log(`✅ API calls successful: ${apiCallsSuccess}`);
    console.log(`❌ API calls failed: ${apiCallsFailed}`);
    console.log(`❌ Console errors: ${errors.length}`);
    
    // Expect API calls to be working
    expect(apiCallsSuccess).toBeGreaterThan(0);
    expect(apiCallsFailed).toBe(0);
    expect(errors.length).toBe(0);
    
    console.log('\\n🎉 All tests passed! Dashboard is fully functional.');
  });
});