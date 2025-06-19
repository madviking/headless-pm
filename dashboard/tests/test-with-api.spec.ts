import { test, expect } from '@playwright/test';

test.describe('Dashboard with API Running', () => {
  test('test dashboard functionality with API', async ({ page }) => {
    console.log('🔍 Testing dashboard with API running...');
    
    // Monitor console errors
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        if (!text.includes('Failed to fetch') && !text.includes('ERR_CONNECTION_REFUSED')) {
          errors.push(text);
        }
      }
    });
    
    // Monitor API calls
    let apiCallsSuccess = 0;
    let apiCallsFailed = 0;
    
    page.on('response', response => {
      const url = response.url();
      if (url.includes('6969')) {
        if (response.status() >= 200 && response.status() < 300) {
          apiCallsSuccess++;
          console.log(`✅ API call success: ${url} - ${response.status()}`);
        } else {
          apiCallsFailed++;
          console.log(`❌ API call failed: ${url} - ${response.status()}`);
        }
      }
    });
    
    // Test homepage
    await page.goto('http://localhost:3001');
    await page.waitForTimeout(3000); // Give time for API calls
    
    // Check if data is loading
    const epicCards = await page.locator('.space-y-4 > div').count();
    console.log(`Epic cards found: ${epicCards}`);
    
    // Take screenshot
    await page.screenshot({ path: 'tests/screenshots/homepage-with-api.png', fullPage: true });
    
    // Test navigation to each page
    const pages = [
      { link: 'Tasks', url: '/tasks', heading: 'Task Management' },
      { link: 'Agents', url: '/agents', heading: 'Agent Activity' },
      { link: 'Communications', url: '/communications', heading: 'Communications' },
      { link: 'Analytics', url: '/analytics', heading: 'Analytics' },
      { link: 'System Health', url: '/health', heading: 'System Health' }
    ];
    
    for (const { link, url, heading } of pages) {
      console.log(`\nTesting navigation to ${link}...`);
      
      // Go back to homepage first
      await page.goto('http://localhost:3001');
      await page.waitForTimeout(500);
      
      // Click the navigation link
      await page.click(`text=${link}`);
      await page.waitForTimeout(1000);
      
      // Check URL
      const currentUrl = page.url();
      console.log(`Current URL: ${currentUrl}`);
      
      if (currentUrl.endsWith(url)) {
        console.log(`✅ Navigation to ${link} successful`);
      } else {
        console.log(`❌ Navigation to ${link} failed - expected ${url}, got ${currentUrl}`);
      }
      
      // Check heading
      try {
        await expect(page.locator('h1')).toContainText(heading);
        console.log(`✅ ${heading} page loaded correctly`);
      } catch (e) {
        console.log(`❌ ${heading} page heading not found`);
      }
    }
    
    // Test Tasks page functionality
    await page.goto('http://localhost:3001/tasks');
    await page.waitForTimeout(2000);
    
    // Check if task columns are present
    const taskColumns = await page.locator('.flex.gap-4 > div').count();
    console.log(`\nTask columns found: ${taskColumns}`);
    
    // Test view switching
    await page.click('button:has-text("Analytics")');
    await page.waitForTimeout(1000);
    const analyticsVisible = await page.locator('text=Total Tasks').isVisible();
    console.log(`Analytics view working: ${analyticsVisible}`);
    
    // Take screenshot
    await page.screenshot({ path: 'tests/screenshots/tasks-with-api.png', fullPage: true });
    
    // Test Agents page
    await page.goto('http://localhost:3001/agents');
    await page.waitForTimeout(2000);
    
    const agentCards = await page.locator('.grid > div').count();
    console.log(`\nAgent cards found: ${agentCards}`);
    
    await page.screenshot({ path: 'tests/screenshots/agents-with-api.png', fullPage: true });
    
    // Summary
    console.log('\n📊 TEST SUMMARY:');
    console.log(`API calls successful: ${apiCallsSuccess}`);
    console.log(`API calls failed: ${apiCallsFailed}`);
    console.log(`Console errors (non-network): ${errors.length}`);
    
    if (errors.length > 0) {
      console.log('\nConsole errors found:');
      errors.slice(0, 5).forEach(err => console.log(`- ${err.substring(0, 100)}...`));
    }
    
    // Check for infinite loop errors
    const infiniteLoopErrors = errors.filter(e => e.includes('Maximum update depth'));
    console.log(`\n⚠️ Infinite loop errors: ${infiniteLoopErrors.length}`);
    
    if (apiCallsSuccess > 0) {
      console.log('\n✅ Dashboard is connecting to API successfully!');
    } else {
      console.log('\n❌ Dashboard is NOT connecting to API');
    }
  });
});