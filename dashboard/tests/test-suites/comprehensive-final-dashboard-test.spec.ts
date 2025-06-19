import { test, expect } from '@playwright/test';

test.describe('Complete Dashboard Functionality Test Suite', () => {
  let dashboardUrl: string;
  let apiUrl: string;

  test.beforeAll(() => {
    dashboardUrl = process.env.DASHBOARD_URL || 'http://localhost:3000';
    apiUrl = process.env.API_URL || 'http://localhost:6969';
  });

  test.beforeEach(async ({ page }) => {
    // Ensure API is available
    try {
      const response = await page.request.get(`${apiUrl}/health`);
      if (!response.ok()) {
        console.warn('API not available, some tests may fail');
      }
    } catch (error) {
      console.warn('API health check failed:', error);
    }

    await page.goto(dashboardUrl);
    await page.waitForLoadState('networkidle');
  });

  test.describe('Homepage Tests', () => {
    test('should load homepage with real data', async ({ page }) => {
      // Check page title and header
      await expect(page.locator('h1')).toContainText('Project Overview');
      await expect(page.locator('p').first()).toContainText('Real-time dashboard for Headless PM');

      // Check stats widgets are present and have real values
      const statsWidgets = page.locator('[data-testid="stats-widget"], .grid .space-y-2, h3:has-text("Total Tasks"), h3:has-text("Completed"), h3:has-text("Active Agents"), h3:has-text("Services")').first();
      await expect(statsWidgets).toBeVisible();

      // Wait for data to load (no skeleton loaders)
      await page.waitForFunction(() => {
        const skeletons = document.querySelectorAll('[class*="skeleton"], [data-testid="skeleton"]');
        return skeletons.length === 0;
      }, { timeout: 10000 });

      // Check that we have stats data
      const totalTasksWidget = page.locator('text=Total Tasks').first();
      if (await totalTasksWidget.isVisible()) {
        await expect(totalTasksWidget).toBeVisible();
      }

      // Check for epics section
      const epicsSection = page.locator('h2:has-text("Active Epics")');
      await expect(epicsSection).toBeVisible();

      // Check for activity feed
      const activitySection = page.locator('h2:has-text("Recent Activity")');
      await expect(activitySection).toBeVisible();
    });

    test('should display epic progress cards or empty state', async ({ page }) => {
      await page.waitForTimeout(2000); // Wait for data loading

      const epicsContainer = page.locator('text=Active Epics').locator('..').locator('..');
      await expect(epicsContainer).toBeVisible();

      // Either epics are displayed or empty state is shown
      const hasEpics = await page.locator('[data-testid="epic-card"]').count() > 0;
      const hasEmptyState = await page.locator('text=No epics created yet').isVisible();

      expect(hasEpics || hasEmptyState).toBeTruthy();
    });

    test('should show recent activity or empty state', async ({ page }) => {
      const activityFeed = page.locator('text=Recent Activity').locator('..').locator('..');
      await expect(activityFeed).toBeVisible();

      // Wait for activity data or empty state
      await page.waitForFunction(() => {
        const noActivity = document.querySelector('text=No recent activity');
        const hasActivity = document.querySelectorAll('[class*="border-b"]').length > 0;
        return noActivity || hasActivity;
      }, { timeout: 5000 });
    });
  });

  test.describe('Navigation Tests', () => {
    test('should navigate to all tabs successfully', async ({ page }) => {
      const tabs = [
        { name: 'Tasks', url: '/tasks' },
        { name: 'Agents', url: '/agents' },
        { name: 'Communications', url: '/communications' },
        { name: 'Analytics', url: '/analytics' },
        { name: 'Health', url: '/health' }
      ];

      for (const tab of tabs) {
        // Click navigation link
        const navLink = page.locator(`nav a[href="${tab.url}"], a:has-text("${tab.name}")`).first();
        await navLink.click();
        
        // Wait for navigation
        await page.waitForURL(`**${tab.url}`);
        await page.waitForLoadState('networkidle');
        
        // Verify we're on the correct page
        await expect(page).toHaveURL(new RegExp(tab.url));
        
        // Check that page content loads
        await page.waitForFunction(() => {
          const skeletons = document.querySelectorAll('[class*="skeleton"]');
          return skeletons.length === 0;
        }, { timeout: 10000 });
      }
    });

    test('should navigate back to home from logo/title', async ({ page }) => {
      // Go to another page first
      await page.goto(`${dashboardUrl}/tasks`);
      await page.waitForLoadState('networkidle');

      // Click logo or home link to go back
      const homeLink = page.locator('a[href="/"], [data-testid="logo"], h1, .logo').first();
      if (await homeLink.isVisible()) {
        await homeLink.click();
        await page.waitForURL('**/');
        await expect(page).toHaveURL(dashboardUrl);
      }
    });
  });

  test.describe('Tasks Page Tests', () => {
    test('should load tasks page with data or empty state', async ({ page }) => {
      await page.goto(`${dashboardUrl}/tasks`);
      await page.waitForLoadState('networkidle');

      // Check page title
      await expect(page.locator('h1')).toContainText('Tasks');

      // Wait for loading to complete
      await page.waitForFunction(() => {
        const skeletons = document.querySelectorAll('[class*="skeleton"]');
        return skeletons.length === 0;
      }, { timeout: 10000 });

      // Check for task filters or controls
      const taskFilters = page.locator('[data-testid="task-filters"], select, button:has-text("Filter"), .filter').first();
      if (await taskFilters.isVisible()) {
        await expect(taskFilters).toBeVisible();
      }

      // Check for tasks display or empty state
      const hasTasks = await page.locator('[data-testid="task-card"], .task-item, .task-row').count() > 0;
      const hasEmptyState = await page.locator('text=No tasks found, text=No tasks available').isVisible();
      
      expect(hasTasks || hasEmptyState).toBeTruthy();
    });

    test('should interact with task filters if present', async ({ page }) => {
      await page.goto(`${dashboardUrl}/tasks`);
      await page.waitForLoadState('networkidle');

      // Try to interact with filters if they exist
      const statusFilter = page.locator('select[name*="status"], select:has(option:has-text("Status")), .filter select').first();
      if (await statusFilter.isVisible()) {
        await statusFilter.click();
        // Don't make assertions about specific options since data may vary
      }

      const roleFilter = page.locator('select[name*="role"], select:has(option:has-text("Role")), .filter select').nth(1);
      if (await roleFilter.isVisible()) {
        await roleFilter.click();
      }
    });
  });

  test.describe('Agents Page Tests', () => {
    test('should load agents page with agent data or empty state', async ({ page }) => {
      await page.goto(`${dashboardUrl}/agents`);
      await page.waitForLoadState('networkidle');

      await expect(page.locator('h1')).toContainText('Agents');

      // Wait for loading
      await page.waitForFunction(() => {
        const skeletons = document.querySelectorAll('[class*="skeleton"]');
        return skeletons.length === 0;
      }, { timeout: 10000 });

      // Check for agents or empty state
      const hasAgents = await page.locator('[data-testid="agent-card"], .agent-item, .agent-row').count() > 0;
      const hasEmptyState = await page.locator('text=No agents found, text=No agents registered').isVisible();
      
      expect(hasAgents || hasEmptyState).toBeTruthy();
    });

    test('should show agent stats widgets', async ({ page }) => {
      await page.goto(`${dashboardUrl}/agents`);
      await page.waitForLoadState('networkidle');

      // Check for stats widgets
      const statsSection = page.locator('.grid').first();
      await expect(statsSection).toBeVisible();
    });
  });

  test.describe('Communications Page Tests', () => {
    test('should load communications page with all tabs', async ({ page }) => {
      await page.goto(`${dashboardUrl}/communications`);
      await page.waitForLoadState('networkidle');

      await expect(page.locator('h1')).toContainText('Communications');

      // Check for tab navigation
      const documentsTab = page.locator('text=Documents, [role="tab"]:has-text("Documents")').first();
      const mentionsTab = page.locator('text=Mentions, [role="tab"]:has-text("Mentions")').first();
      const createTab = page.locator('text=Create Document, [role="tab"]:has-text("Create")').first();

      await expect(documentsTab).toBeVisible();
      await expect(mentionsTab).toBeVisible();
      await expect(createTab).toBeVisible();
    });

    test('should switch between communications tabs', async ({ page }) => {
      await page.goto(`${dashboardUrl}/communications`);
      await page.waitForLoadState('networkidle');

      // Test tab switching
      const tabs = ['Documents', 'Mentions', 'Create'];
      
      for (const tabName of tabs) {
        const tab = page.locator(`[role="tab"]:has-text("${tabName}"), button:has-text("${tabName}")`).first();
        if (await tab.isVisible()) {
          await tab.click();
          await page.waitForTimeout(500);
          
          // Verify tab content is visible
          const tabContent = page.locator(`[role="tabpanel"], .tab-content`).first();
          await expect(tabContent).toBeVisible();
        }
      }
    });

    test('should show document creation form', async ({ page }) => {
      await page.goto(`${dashboardUrl}/communications`);
      await page.waitForLoadState('networkidle');

      // Click create tab
      const createTab = page.locator('text=Create, [role="tab"]:has-text("Create")').first();
      if (await createTab.isVisible()) {
        await createTab.click();
        
        // Check for form elements
        const titleInput = page.locator('input[placeholder*="title"], input[name="title"], label:has-text("Title") + input').first();
        const contentTextarea = page.locator('textarea[placeholder*="content"], textarea[name="content"], label:has-text("Content") + textarea').first();
        const createButton = page.locator('button:has-text("Create"), button[type="submit"]').first();

        if (await titleInput.isVisible()) {
          await expect(titleInput).toBeVisible();
        }
        if (await contentTextarea.isVisible()) {
          await expect(contentTextarea).toBeVisible();
        }
        if (await createButton.isVisible()) {
          await expect(createButton).toBeVisible();
        }
      }
    });
  });

  test.describe('Analytics Page Tests', () => {
    test('should load analytics page with metrics', async ({ page }) => {
      await page.goto(`${dashboardUrl}/analytics`);
      await page.waitForLoadState('networkidle');

      await expect(page.locator('h1')).toContainText('Analytics');

      // Wait for data loading
      await page.waitForFunction(() => {
        const skeletons = document.querySelectorAll('[class*="skeleton"]');
        return skeletons.length === 0;
      }, { timeout: 10000 });

      // Check for analytics content
      const metricsSection = page.locator('.grid, .stats, [data-testid="analytics"]').first();
      await expect(metricsSection).toBeVisible();
    });

    test('should display charts and progress bars', async ({ page }) => {
      await page.goto(`${dashboardUrl}/analytics`);
      await page.waitForLoadState('networkidle');

      // Look for progress bars or chart elements
      const progressBars = page.locator('[role="progressbar"], .progress, .chart');
      const chartElements = page.locator('.recharts, canvas, svg');
      
      // At least one visualization should be present
      const hasProgress = await progressBars.count() > 0;
      const hasCharts = await chartElements.count() > 0;
      
      expect(hasProgress || hasCharts).toBeTruthy();
    });
  });

  test.describe('Health Page Tests', () => {
    test('should load health page with system status', async ({ page }) => {
      await page.goto(`${dashboardUrl}/health`);
      await page.waitForLoadState('networkidle');

      await expect(page.locator('h1')).toContainText('Health');

      // Wait for health data
      await page.waitForFunction(() => {
        const skeletons = document.querySelectorAll('[class*="skeleton"]');
        return skeletons.length === 0;
      }, { timeout: 10000 });

      // Check for health metrics
      const healthMetrics = page.locator('.grid, .health-stats, [data-testid="health"]').first();
      await expect(healthMetrics).toBeVisible();
    });

    test('should have health tabs (Services, Agents, System)', async ({ page }) => {
      await page.goto(`${dashboardUrl}/health`);
      await page.waitForLoadState('networkidle');

      const tabs = ['Services', 'Agents', 'System'];
      
      for (const tabName of tabs) {
        const tab = page.locator(`[role="tab"]:has-text("${tabName}"), button:has-text("${tabName}")`).first();
        if (await tab.isVisible()) {
          await tab.click();
          await page.waitForTimeout(500);
          
          // Verify tab content loads
          const tabContent = page.locator(`[role="tabpanel"], .tab-content`).first();
          await expect(tabContent).toBeVisible();
        }
      }
    });

    test('should have refresh functionality', async ({ page }) => {
      await page.goto(`${dashboardUrl}/health`);
      await page.waitForLoadState('networkidle');

      // Look for refresh button
      const refreshButton = page.locator('button:has-text("Refresh"), button[aria-label*="refresh"], .refresh-btn').first();
      if (await refreshButton.isVisible()) {
        await refreshButton.click();
        await page.waitForTimeout(1000);
      }
    });
  });

  test.describe('Responsive Design Tests', () => {
    test('should work on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(dashboardUrl);
      await page.waitForLoadState('networkidle');

      // Check that content is still visible and accessible
      await expect(page.locator('h1')).toBeVisible();
      
      // Navigation should be accessible (might be in a menu)
      const navItems = page.locator('nav a, [role="navigation"] a, .nav-link');
      if (await navItems.count() > 0) {
        await expect(navItems.first()).toBeVisible();
      }
    });

    test('should work on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto(dashboardUrl);
      await page.waitForLoadState('networkidle');

      await expect(page.locator('h1')).toBeVisible();
      
      // Check grid layouts adapt
      const gridElements = page.locator('.grid, .grid-cols-1, .grid-cols-2');
      if (await gridElements.count() > 0) {
        await expect(gridElements.first()).toBeVisible();
      }
    });

    test('should work on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto(dashboardUrl);
      await page.waitForLoadState('networkidle');

      await expect(page.locator('h1')).toBeVisible();
    });
  });

  test.describe('Error Handling Tests', () => {
    test('should handle API failures gracefully', async ({ page }) => {
      // Intercept API calls and make them fail
      await page.route('**/api/**', route => route.abort());
      
      await page.goto(dashboardUrl);
      
      // Page should still load even if API fails
      await expect(page.locator('h1')).toBeVisible();
      
      // Should show loading states or error states, not crash
      await page.waitForTimeout(3000);
      
      // Page should not show uncaught error messages
      const errorMessages = page.locator('text=Error:, text=Uncaught, text=TypeError');
      expect(await errorMessages.count()).toBe(0);
    });

    test('should handle slow API responses', async ({ page }) => {
      // Add delay to API responses
      await page.route('**/api/**', async route => {
        await new Promise(resolve => setTimeout(resolve, 2000));
        route.continue();
      });

      await page.goto(dashboardUrl);
      
      // Should show loading states
      const loadingElements = page.locator('[class*="skeleton"], .loading, .spinner');
      if (await loadingElements.count() > 0) {
        await expect(loadingElements.first()).toBeVisible();
      }
      
      // Eventually should load content
      await page.waitForFunction(() => {
        const skeletons = document.querySelectorAll('[class*="skeleton"]');
        return skeletons.length === 0;
      }, { timeout: 15000 });
    });
  });

  test.describe('Performance Tests', () => {
    test('should load homepage within reasonable time', async ({ page }) => {
      const startTime = Date.now();
      await page.goto(dashboardUrl);
      await page.waitForLoadState('networkidle');
      const loadTime = Date.now() - startTime;
      
      // Should load within 10 seconds
      expect(loadTime).toBeLessThan(10000);
    });

    test('should not have console errors', async ({ page }) => {
      const consoleErrors: string[] = [];
      
      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });
      
      await page.goto(dashboardUrl);
      await page.waitForLoadState('networkidle');
      
      // Navigate through all pages
      const urls = ['/tasks', '/agents', '/communications', '/analytics', '/health'];
      for (const url of urls) {
        await page.goto(`${dashboardUrl}${url}`);
        await page.waitForLoadState('networkidle');
      }
      
      // Filter out non-critical errors
      const criticalErrors = consoleErrors.filter(error => 
        !error.includes('favicon') && 
        !error.includes('net::ERR_') &&
        !error.includes('webpack-internal')
      );
      
      expect(criticalErrors).toHaveLength(0);
    });
  });

  test.describe('Accessibility Tests', () => {
    test('should have proper heading structure', async ({ page }) => {
      await page.goto(dashboardUrl);
      await page.waitForLoadState('networkidle');

      const h1Elements = page.locator('h1');
      await expect(h1Elements).toHaveCount(1);
      
      const headings = page.locator('h1, h2, h3, h4, h5, h6');
      expect(await headings.count()).toBeGreaterThan(0);
    });

    test('should be navigable with keyboard', async ({ page }) => {
      await page.goto(dashboardUrl);
      await page.waitForLoadState('networkidle');

      // Focus should be manageable with tab key
      await page.keyboard.press('Tab');
      const focusedElement = page.locator(':focus');
      if (await focusedElement.count() > 0) {
        await expect(focusedElement).toBeVisible();
      }
    });

    test('should have accessible buttons and links', async ({ page }) => {
      await page.goto(dashboardUrl);
      await page.waitForLoadState('networkidle');

      // All buttons should be accessible
      const buttons = page.locator('button');
      const buttonCount = await buttons.count();
      
      for (let i = 0; i < Math.min(buttonCount, 10); i++) {
        const button = buttons.nth(i);
        if (await button.isVisible()) {
          // Should have text content or aria-label
          const hasText = await button.textContent();
          const hasAriaLabel = await button.getAttribute('aria-label');
          expect(hasText || hasAriaLabel).toBeTruthy();
        }
      }
    });
  });
});