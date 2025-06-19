import { test, expect } from '@playwright/test';

test('Debug API Connection Issues', async ({ page }) => {
  console.log('🔍 Debugging API connection...');
  
  // Enable detailed logging
  const apiRequests: any[] = [];
  const consoleMessages: any[] = [];
  
  // Log all console messages
  page.on('console', msg => {
    const text = msg.text();
    consoleMessages.push({ type: msg.type(), text });
    if (msg.type() === 'error') {
      console.log(`Console Error: ${text}`);
    }
  });
  
  // Log all network requests
  page.on('request', request => {
    const url = request.url();
    if (url.includes('localhost:6969') || url.includes('/api/')) {
      console.log(`🔵 API Request: ${request.method()} ${url}`);
      apiRequests.push({
        method: request.method(),
        url: url,
        headers: request.headers()
      });
    }
  });
  
  // Log all network responses
  page.on('response', response => {
    const url = response.url();
    if (url.includes('localhost:6969') || url.includes('/api/')) {
      console.log(`🟢 API Response: ${response.status()} ${url}`);
    }
  });
  
  // Log failed requests
  page.on('requestfailed', request => {
    const url = request.url();
    if (url.includes('localhost:6969') || url.includes('/api/')) {
      console.log(`🔴 Request Failed: ${url} - ${request.failure()?.errorText}`);
    }
  });
  
  // Navigate to homepage
  await page.goto('http://localhost:3001');
  console.log('📍 Navigated to homepage');
  
  // Wait for potential API calls
  await page.waitForTimeout(5000);
  
  // Check if any API requests were made
  console.log(`\n📊 API Requests Made: ${apiRequests.length}`);
  
  // Check page content
  const pageContent = await page.content();
  console.log('\n🔍 Checking page content for data...');
  
  // Look for signs of data
  const hasEpics = pageContent.includes('Epic');
  const hasTasks = pageContent.includes('Task');
  const hasAgents = pageContent.includes('Agent');
  
  console.log(`Has Epic content: ${hasEpics}`);
  console.log(`Has Task content: ${hasTasks}`);
  console.log(`Has Agent content: ${hasAgents}`);
  
  // Check specific elements
  const totalTasks = await page.locator('text=Total Tasks').isVisible();
  const taskCount = await page.locator('text=Total Tasks').locator('..').locator('div').first().textContent();
  console.log(`\nTotal Tasks visible: ${totalTasks}`);
  console.log(`Task count shows: ${taskCount}`);
  
  // Navigate to tasks page
  await page.goto('http://localhost:3001/tasks');
  await page.waitForTimeout(3000);
  
  console.log('\n📍 Navigated to Tasks page');
  console.log(`Total API requests so far: ${apiRequests.length}`);
  
  // Check for task data
  const taskBoardVisible = await page.locator('.flex.gap-4').isVisible();
  console.log(`Task board visible: ${taskBoardVisible}`);
  
  // Try to make a direct API call from the browser
  const apiTestResult = await page.evaluate(async () => {
    try {
      const response = await fetch('http://localhost:6969/api/v1/context');
      return {
        ok: response.ok,
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      };
    } catch (error: any) {
      return {
        error: error.message,
        stack: error.stack
      };
    }
  });
  
  console.log('\n🔬 Direct API call test:');
  console.log(JSON.stringify(apiTestResult, null, 2));
  
  // Check environment variables
  const envVars = await page.evaluate(() => {
    return {
      API_URL: process.env.NEXT_PUBLIC_API_URL,
      // Check if window has any API config
      windowConfig: (window as any).__NEXT_DATA__?.props?.pageProps
    };
  });
  
  console.log('\n🔧 Environment variables:');
  console.log(JSON.stringify(envVars, null, 2));
  
  // Summary
  console.log('\n📋 SUMMARY:');
  console.log(`- API requests made: ${apiRequests.length}`);
  console.log(`- Console errors: ${consoleMessages.filter(m => m.type === 'error').length}`);
  console.log(`- Page has data: ${hasEpics || hasTasks || hasAgents}`);
  
  if (apiRequests.length === 0) {
    console.log('\n❌ PROBLEM: No API requests are being made!');
    console.log('Possible causes:');
    console.log('1. React Query is not fetching data');
    console.log('2. Components are not mounting properly');
    console.log('3. API client is not initialized');
  }
  
  // Take screenshot for debugging
  await page.screenshot({ path: 'tests/screenshots/debug-api.png', fullPage: true });
});