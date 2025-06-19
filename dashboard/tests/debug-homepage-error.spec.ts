import { test, expect } from '@playwright/test';

test('Debug Homepage Internal Server Error', async ({ page }) => {
  console.log('🔍 Debugging homepage server error...');
  
  // Capture console errors
  const consoleErrors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const text = msg.text();
      consoleErrors.push(text);
      console.log(`❌ Console Error: ${text}`);
    }
  });
  
  // Capture page errors
  const pageErrors: string[] = [];
  page.on('pageerror', err => {
    pageErrors.push(err.message);
    console.log(`💥 Page Error: ${err.message}`);
  });
  
  // Capture network failures
  page.on('requestfailed', request => {
    console.log(`🔴 Request Failed: ${request.url()} - ${request.failure()?.errorText}`);
  });
  
  try {
    console.log('📍 Attempting to navigate to homepage...');
    const response = await page.goto('http://localhost:3001', { timeout: 10000 });
    
    if (response) {
      console.log(`🌐 Response status: ${response.status()}`);
      console.log(`🌐 Response headers: ${JSON.stringify(await response.allHeaders())}`);
      
      if (response.status() >= 400) {
        const text = await response.text();
        console.log(`📄 Response body: ${text.substring(0, 500)}`);
      }
    }
    
    // Wait for any potential content to load
    await page.waitForTimeout(3000);
    
    // Check page title
    const title = await page.title();
    console.log(`📋 Page title: "${title}"`);
    
    // Check if there's any content
    const bodyText = await page.locator('body').textContent();
    console.log(`📄 Body content preview: "${bodyText?.substring(0, 200)}"`);
    
    // Take screenshot for debugging
    await page.screenshot({ path: 'tests/screenshots/homepage-error.png', fullPage: true });
    
  } catch (error) {
    console.log(`💥 Navigation error: ${error}`);
  }
  
  console.log(`\\n📊 SUMMARY:`);
  console.log(`- Console errors: ${consoleErrors.length}`);
  console.log(`- Page errors: ${pageErrors.length}`);
  
  if (consoleErrors.length > 0) {
    console.log('\\n❌ Console errors found:');
    consoleErrors.forEach(err => console.log(`  - ${err}`));
  }
  
  if (pageErrors.length > 0) {
    console.log('\\n💥 Page errors found:');
    pageErrors.forEach(err => console.log(`  - ${err}`));
  }
});