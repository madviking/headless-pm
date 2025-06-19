import { test, expect } from '@playwright/test';

test.describe('Dashboard Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the dashboard
    await page.goto('http://localhost:3001');
  });

  test('should load the homepage with overview', async ({ page }) => {
    // Check if the page loads
    await expect(page).toHaveTitle(/Dashboard/);
    
    // Check for main navigation
    await expect(page.locator('text=Overview')).toBeVisible();
    await expect(page.locator('text=Tasks')).toBeVisible();
    await expect(page.locator('text=Agents')).toBeVisible();
    
    // Check for main content
    await expect(page.locator('h1:has-text("Project Overview")')).toBeVisible();
    
    // Take a screenshot of the homepage
    await page.screenshot({ path: 'tests/screenshots/homepage.png', fullPage: true });
  });

  test('should navigate to Tasks page and show Kanban board', async ({ page }) => {
    // Navigate to Tasks page
    await page.click('text=Tasks');
    
    // Wait for page to load
    await expect(page.locator('h1:has-text("Task Management")')).toBeVisible();
    
    // Check for view tabs
    await expect(page.locator('text=Board')).toBeVisible();
    await expect(page.locator('text=Timeline')).toBeVisible();
    await expect(page.locator('text=Analytics')).toBeVisible();
    
    // Check for filter section
    await expect(page.locator('text=Epic:')).toBeVisible();
    await expect(page.locator('text=Role:')).toBeVisible();
    await expect(page.locator('text=Search:')).toBeVisible();
    
    // Wait for potential API calls and check for Kanban columns
    await page.waitForTimeout(2000);
    
    // Check if Kanban board structure is present (even if no data)
    const boardContainer = page.locator('[class*="flex gap-4 overflow-x-auto"]');
    await expect(boardContainer).toBeVisible({ timeout: 10000 });
    
    // Take a screenshot of the tasks page
    await page.screenshot({ path: 'tests/screenshots/tasks-page.png', fullPage: true });
    
    console.log('Tasks page loaded successfully');
  });

  test('should navigate to Agents page and show agent grid', async ({ page }) => {
    // Navigate to Agents page
    await page.click('text=Agents');
    
    // Wait for page to load
    await expect(page.locator('h1:has-text("Agent Activity")')).toBeVisible();
    
    // Wait for potential API calls
    await page.waitForTimeout(2000);
    
    // Check for agent stats section
    await expect(page.locator('text=Total Agents')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Active Workers')).toBeVisible();
    
    // Check for agent status section
    await expect(page.locator('text=Agent Status')).toBeVisible();
    
    // Check for activity feed
    await expect(page.locator('text=Live Activity Feed')).toBeVisible();
    
    // Take a screenshot of the agents page
    await page.screenshot({ path: 'tests/screenshots/agents-page.png', fullPage: true });
    
    console.log('Agents page loaded successfully');
  });

  test('should test task filters functionality', async ({ page }) => {
    // Navigate to Tasks page
    await page.click('text=Tasks');
    await page.waitForTimeout(1000);
    
    // Test epic filter
    const epicSelect = page.locator('select').first();
    await epicSelect.selectOption('authentication');
    await page.waitForTimeout(500);
    
    // Test role filter
    const roleSelect = page.locator('select').nth(1);
    await roleSelect.selectOption('frontend_dev');
    await page.waitForTimeout(500);
    
    // Test search
    const searchInput = page.locator('input[placeholder*="Search"]');
    await searchInput.fill('login');
    await page.waitForTimeout(500);
    
    // Clear filters
    const clearButton = page.locator('text=Clear Filters');
    if (await clearButton.isVisible()) {
      await clearButton.click();
    }
    
    console.log('Filter functionality tested');
  });

  test('should test view switching', async ({ page }) => {
    // Navigate to Tasks page
    await page.click('text=Tasks');
    await page.waitForTimeout(1000);
    
    // Test Timeline view
    await page.click('text=Timeline');
    await page.waitForTimeout(1000);
    await expect(page.locator('text=Task Timeline')).toBeVisible({ timeout: 5000 });
    
    // Test Analytics view
    await page.click('text=Analytics');
    await page.waitForTimeout(1000);
    await expect(page.locator('text=Total Tasks')).toBeVisible({ timeout: 5000 });
    
    // Go back to Board view
    await page.click('text=Board');
    await page.waitForTimeout(1000);
    
    console.log('View switching tested');
  });

  test('should check for console errors', async ({ page }) => {
    const errors: string[] = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // Navigate through all pages
    await page.click('text=Tasks');
    await page.waitForTimeout(2000);
    
    await page.click('text=Agents');
    await page.waitForTimeout(2000);
    
    await page.click('text=Overview');
    await page.waitForTimeout(2000);
    
    // Report any console errors
    if (errors.length > 0) {
      console.log('Console errors found:', errors);
    } else {
      console.log('No console errors detected');
    }
  });

  test('should check API connectivity', async ({ page }) => {
    let apiCallsDetected = false;
    
    page.on('request', request => {
      const url = request.url();
      if (url.includes('/api/v1/') || url.includes('6969')) {
        apiCallsDetected = true;
        console.log('API call detected:', url);
      }
    });
    
    page.on('response', response => {
      const url = response.url();
      if (url.includes('/api/v1/') || url.includes('6969')) {
        console.log('API response:', url, response.status());
      }
    });
    
    // Navigate to different pages to trigger API calls
    await page.click('text=Tasks');
    await page.waitForTimeout(3000);
    
    await page.click('text=Agents');
    await page.waitForTimeout(3000);
    
    console.log('API calls detected:', apiCallsDetected);
  });
});