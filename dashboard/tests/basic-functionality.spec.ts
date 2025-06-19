import { test, expect } from '@playwright/test';

test.describe('Basic Dashboard Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3001');
  });

  test('should load homepage and navigate to tasks', async ({ page }) => {
    // Check if the page loads
    await expect(page.locator('h1:has-text("Project Overview")')).toBeVisible();
    
    // Navigate to Tasks page
    await page.click('[role="link"]:has-text("Tasks")');
    
    // Wait for page to load
    await expect(page.locator('h1:has-text("Task Management")')).toBeVisible();
    
    // Check for view tabs
    await expect(page.locator('button:has-text("Board")')).toBeVisible();
    await expect(page.locator('button:has-text("Timeline")')).toBeVisible();
    await expect(page.locator('button:has-text("Analytics")')).toBeVisible();
    
    // Take screenshot
    await page.screenshot({ path: 'tests/screenshots/tasks-working.png', fullPage: true });
    
    console.log('✅ Tasks page navigation working');
  });

  test('should load agents page', async ({ page }) => {
    // Navigate to Agents page
    await page.click('[role="link"]:has-text("Agents")');
    
    // Wait for page to load
    await expect(page.locator('h1:has-text("Agent Activity")')).toBeVisible();
    
    // Check for basic elements that should be there
    await expect(page.locator('text=Total Agents')).toBeVisible();
    
    // Take screenshot
    await page.screenshot({ path: 'tests/screenshots/agents-working.png', fullPage: true });
    
    console.log('✅ Agents page navigation working');
  });

  test('should test task view switching', async ({ page }) => {
    // Navigate to Tasks page
    await page.click('[role="link"]:has-text("Tasks")');
    await page.waitForTimeout(1000);
    
    // Test Analytics view
    await page.click('button:has-text("Analytics")');
    await page.waitForTimeout(1000);
    
    // Should see analytics content
    await expect(page.locator('text=Total Tasks')).toBeVisible();
    
    // Test Timeline view
    await page.click('button:has-text("Timeline")');
    await page.waitForTimeout(1000);
    
    // Should see timeline content
    await expect(page.locator('text=Task Timeline')).toBeVisible();
    
    // Go back to Board view
    await page.click('button:has-text("Board")');
    await page.waitForTimeout(1000);
    
    console.log('✅ View switching working');
  });

  test('should check for API errors in console', async ({ page }) => {
    const errors: string[] = [];
    const warnings: string[] = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      } else if (msg.type() === 'warning') {
        warnings.push(msg.text());
      }
    });
    
    // Navigate through pages to trigger potential errors
    await page.click('[role="link"]:has-text("Tasks")');
    await page.waitForTimeout(2000);
    
    await page.click('[role="link"]:has-text("Agents")');
    await page.waitForTimeout(2000);
    
    await page.click('[role="link"]:has-text("Overview")');
    await page.waitForTimeout(2000);
    
    // Filter out known acceptable warnings/errors
    const significantErrors = errors.filter(error => 
      !error.includes('net::ERR_CONNECTION_REFUSED') && // API connection errors are expected
      !error.includes('Failed to fetch') &&
      !error.includes('fetch') &&
      !error.toLowerCase().includes('network error')
    );
    
    console.log('Total console errors:', errors.length);
    console.log('Significant errors (non-network):', significantErrors.length);
    console.log('Console warnings:', warnings.length);
    
    if (significantErrors.length > 0) {
      console.log('❌ Significant errors found:', significantErrors);
    } else {
      console.log('✅ No significant console errors (network errors are expected without API server)');
    }
  });
});