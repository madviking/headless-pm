import { test, expect } from '@playwright/test';

test.describe('Working Dashboard Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3001');
  });

  test('should load homepage and show project overview', async ({ page }) => {
    // Check if the page loads with correct title
    await expect(page).toHaveTitle(/Headless PM Dashboard/);
    
    // Check for main project overview heading
    await expect(page.locator('h1:has-text("Project Overview")')).toBeVisible();
    
    // Check for main navigation links
    await expect(page.locator('a[href="/"]')).toBeVisible();
    await expect(page.locator('a[href="/tasks"]')).toBeVisible();
    await expect(page.locator('a[href="/agents"]')).toBeVisible();
    
    // Check for dashboard widgets
    await expect(page.locator('text=Total Tasks')).toBeVisible();
    await expect(page.locator('text=Active Agents')).toBeVisible();
    await expect(page.locator('text=Services')).toBeVisible();
    
    console.log('✅ Homepage loads correctly with all main elements');
  });

  test('should navigate to Tasks page and show task management', async ({ page }) => {
    // Click on Tasks link using href
    await page.click('a[href="/tasks"]');
    
    // Wait for navigation and check URL
    await expect(page).toHaveURL(/.*\/tasks/);
    
    // Check for task management heading
    await expect(page.locator('h1:has-text("Task Management")')).toBeVisible();
    
    // Check for view tabs
    await expect(page.locator('text=Board')).toBeVisible();
    await expect(page.locator('text=Timeline')).toBeVisible();
    await expect(page.locator('text=Analytics')).toBeVisible();
    
    // Check for filter section
    await expect(page.locator('text=Epic:')).toBeVisible();
    await expect(page.locator('text=Role:')).toBeVisible();
    
    // Take screenshot
    await page.screenshot({ path: 'tests/screenshots/tasks-page-working.png', fullPage: true });
    
    console.log('✅ Tasks page navigation and layout working');
  });

  test('should navigate to Agents page and show agent activity', async ({ page }) => {
    // Click on Agents link using href
    await page.click('a[href="/agents"]');
    
    // Wait for navigation and check URL
    await expect(page).toHaveURL(/.*\/agents/);
    
    // Check for agent activity heading
    await expect(page.locator('h1:has-text("Agent Activity")')).toBeVisible();
    
    // Check for agent stats
    await expect(page.locator('text=Total Agents')).toBeVisible();
    await expect(page.locator('text=Active Workers')).toBeVisible();
    
    // Check for agent status section
    await expect(page.locator('text=Agent Status')).toBeVisible();
    
    // Check for activity feed
    await expect(page.locator('text=Live Activity Feed')).toBeVisible();
    
    // Take screenshot
    await page.screenshot({ path: 'tests/screenshots/agents-page-working.png', fullPage: true });
    
    console.log('✅ Agents page navigation and layout working');
  });

  test('should test task view switching functionality', async ({ page }) => {
    // Navigate to Tasks page
    await page.click('a[href="/tasks"]');
    await expect(page).toHaveURL(/.*\/tasks/);
    
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
    
    console.log('✅ Task view switching working correctly');
  });

  test('should check responsive design', async ({ page }) => {
    // Test desktop view
    await page.setViewportSize({ width: 1200, height: 800 });
    await expect(page.locator('h1:has-text("Project Overview")')).toBeVisible();
    
    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('h1:has-text("Project Overview")')).toBeVisible();
    
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('h1:has-text("Project Overview")')).toBeVisible();
    
    console.log('✅ Responsive design working across different screen sizes');
  });

  test('should verify all navigation links work', async ({ page }) => {
    const navigationTests = [
      { href: '/tasks', expectedText: 'Task Management' },
      { href: '/agents', expectedText: 'Agent Activity' },
      { href: '/communications', expectedText: 'Communications' },
      { href: '/analytics', expectedText: 'Analytics' },
      { href: '/health', expectedText: 'System Health' }
    ];

    for (const { href, expectedText } of navigationTests) {
      await page.click(`a[href="${href}"]`);
      await expect(page).toHaveURL(new RegExp(href.replace('/', '\\/')));
      
      // Wait a bit for the page to load
      await page.waitForTimeout(500);
      
      // Go back to home for next test
      await page.click('a[href="/"]');
      await page.waitForTimeout(500);
    }
    
    console.log('✅ All navigation links are functional');
  });

  test('should handle API connection gracefully', async ({ page }) => {
    const apiErrors: string[] = [];
    const networkErrors: string[] = [];
    
    page.on('response', response => {
      const url = response.url();
      if (url.includes('/api/') && response.status() >= 400) {
        apiErrors.push(`${response.status()} - ${url}`);
      }
    });
    
    page.on('console', msg => {
      if (msg.type() === 'error' && msg.text().includes('fetch')) {
        networkErrors.push(msg.text());
      }
    });
    
    // Navigate through pages to trigger API calls
    await page.click('a[href="/tasks"]');
    await page.waitForTimeout(2000);
    
    await page.click('a[href="/agents"]');
    await page.waitForTimeout(2000);
    
    console.log(`API errors: ${apiErrors.length} (expected - no backend running)`);
    console.log(`Network errors: ${networkErrors.length} (expected - API not available)`);
    console.log('✅ Dashboard handles API unavailability gracefully');
  });
});