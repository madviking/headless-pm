import { test, expect, Page, ConsoleMessage } from '@playwright/test';
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { join } from 'path';

// Create results directory if it doesn't exist
const resultsDir = join(__dirname, 'test-results');
if (!existsSync(resultsDir)) {
  mkdirSync(resultsDir, { recursive: true });
}

interface TestResult {
  page: string;
  url: string;
  consoleErrors: string[];
  consoleWarnings: string[];
  networkErrors: string[];
  reactErrors: string[];
  uiIssues: string[];
  apiCalls: { url: string; status: number; method: string }[];
  loadTime: number;
  screenshot: string;
}

const results: TestResult[] = [];

test.describe('Comprehensive Dashboard Issue Detection', () => {
  test.beforeEach(async ({ page }) => {
    // Set up console and network monitoring
    const consoleErrors: string[] = [];
    const consoleWarnings: string[] = [];
    const reactErrors: string[] = [];
    const networkErrors: string[] = [];
    const apiCalls: { url: string; status: number; method: string }[] = [];

    // Monitor console messages
    page.on('console', (msg: ConsoleMessage) => {
      const text = msg.text();
      const type = msg.type();
      
      if (type === 'error') {
        if (text.includes('React') || text.includes('Invalid') || text.includes('Cannot read')) {
          reactErrors.push(text);
        }
        consoleErrors.push(text);
      } else if (type === 'warning') {
        consoleWarnings.push(text);
      }
    });

    // Monitor network requests
    page.on('requestfailed', request => {
      networkErrors.push(`${request.method()} ${request.url()} - ${request.failure()?.errorText}`);
    });

    // Monitor API calls
    page.on('response', response => {
      const url = response.url();
      if (url.includes('/api/') || url.includes('localhost:6969')) {
        apiCalls.push({
          url,
          status: response.status(),
          method: response.request().method()
        });
      }
    });

    // Attach to page context for use in tests
    (page as any).testData = {
      consoleErrors,
      consoleWarnings,
      reactErrors,
      networkErrors,
      apiCalls
    };
  });

  const pages = [
    { name: 'Homepage', url: '/' },
    { name: 'Tasks', url: '/tasks' },
    { name: 'Agents', url: '/agents' },
    { name: 'Communications', url: '/communications' },
    { name: 'Analytics', url: '/analytics' },
    { name: 'Health', url: '/health' }
  ];

  for (const pageInfo of pages) {
    test(`Test ${pageInfo.name} - ${pageInfo.url}`, async ({ page }) => {
      const testData = (page as any).testData;
      const startTime = Date.now();
      const uiIssues: string[] = [];

      console.log(`\n🔍 Testing ${pageInfo.name} page...`);

      try {
        // Navigate to page
        await page.goto(`http://localhost:3001${pageInfo.url}`, {
          waitUntil: 'networkidle',
          timeout: 30000
        });
      } catch (error) {
        uiIssues.push(`Navigation failed: ${error}`);
      }

      const loadTime = Date.now() - startTime;

      // Wait for page to stabilize
      await page.waitForTimeout(3000);

      // Take screenshot
      const screenshotPath = join(resultsDir, `${pageInfo.name.toLowerCase().replace(/\s+/g, '-')}.png`);
      await page.screenshot({ 
        path: screenshotPath, 
        fullPage: true 
      });

      // Check for common UI elements
      try {
        // Check if navigation is present
        const nav = await page.locator('nav').count();
        if (nav === 0) {
          uiIssues.push('Navigation component not found');
        }

        // Check for page title/header
        const headers = await page.locator('h1').count();
        if (headers === 0) {
          uiIssues.push('No h1 header found on page');
        }

        // Check for loading states
        const loadingElements = await page.locator('[class*="loading"], [class*="spinner"], [class*="skeleton"]').count();
        if (loadingElements > 0) {
          uiIssues.push(`${loadingElements} loading elements still visible after page load`);
        }

        // Check for error boundaries
        const errorBoundaries = await page.locator('text=/error|failed|exception/i').count();
        if (errorBoundaries > 0) {
          uiIssues.push('Error messages visible on page');
        }

        // Page-specific checks
        switch (pageInfo.url) {
          case '/':
            // Check for epic cards
            const epicCards = await page.locator('[class*="epic"], [class*="Epic"]').count();
            if (epicCards === 0) {
              uiIssues.push('No epic cards found on homepage');
            }
            break;

          case '/tasks':
            // Check for task elements
            const taskElements = await page.locator('[class*="task"], [class*="Task"]').count();
            if (taskElements === 0) {
              uiIssues.push('No task-related elements found');
            }
            
            // Check for view tabs
            const tabs = await page.locator('[role="tab"], button:has-text("Board"), button:has-text("Analytics"), button:has-text("Timeline")').count();
            if (tabs === 0) {
              uiIssues.push('View switching tabs not found');
            }
            break;

          case '/agents':
            // Check for agent grid or list
            const agentElements = await page.locator('[class*="agent"], [class*="Agent"]').count();
            if (agentElements === 0) {
              uiIssues.push('No agent-related elements found');
            }
            break;

          case '/communications':
            // Check for document/message elements
            const commElements = await page.locator('[class*="document"], [class*="message"], [class*="Document"], [class*="Message"]').count();
            if (commElements === 0) {
              uiIssues.push('No communication elements found');
            }
            break;

          case '/analytics':
            // Check for charts or stats
            const analyticsElements = await page.locator('[class*="chart"], [class*="stat"], [class*="Chart"], [class*="Stat"]').count();
            if (analyticsElements === 0) {
              uiIssues.push('No analytics elements found');
            }
            break;

          case '/health':
            // Check for service status elements
            const healthElements = await page.locator('[class*="service"], [class*="health"], [class*="Service"], [class*="Health"]').count();
            if (healthElements === 0) {
              uiIssues.push('No health/service elements found');
            }
            break;
        }

        // Check for broken images
        const images = await page.locator('img').all();
        for (const img of images) {
          const naturalWidth = await img.evaluate((el: HTMLImageElement) => el.naturalWidth);
          if (naturalWidth === 0) {
            const src = await img.getAttribute('src');
            uiIssues.push(`Broken image: ${src}`);
          }
        }

        // Check for React hydration issues
        const bodyHtml = await page.locator('body').innerHTML();
        if (bodyHtml.includes('<!-- -->') && bodyHtml.match(/<!-- -->/g)!.length > 10) {
          uiIssues.push('Possible React hydration issues detected (many empty comments)');
        }

      } catch (error) {
        uiIssues.push(`UI check failed: ${error}`);
      }

      // Save results
      results.push({
        page: pageInfo.name,
        url: pageInfo.url,
        consoleErrors: testData.consoleErrors,
        consoleWarnings: testData.consoleWarnings,
        networkErrors: testData.networkErrors,
        reactErrors: testData.reactErrors,
        uiIssues,
        apiCalls: testData.apiCalls,
        loadTime,
        screenshot: screenshotPath
      });

      // Log immediate findings
      console.log(`📊 ${pageInfo.name} Test Results:`);
      console.log(`  Load time: ${loadTime}ms`);
      console.log(`  Console errors: ${testData.consoleErrors.length}`);
      console.log(`  React errors: ${testData.reactErrors.length}`);
      console.log(`  Network errors: ${testData.networkErrors.length}`);
      console.log(`  UI issues: ${uiIssues.length}`);
      console.log(`  API calls: ${testData.apiCalls.length}`);
      
      if (testData.consoleErrors.length > 0) {
        console.log(`  Sample console errors:`, testData.consoleErrors.slice(0, 3));
      }
    });
  }

  test('Test Navigation Between Pages', async ({ page }) => {
    console.log('\n🔍 Testing navigation between pages...');
    const navigationIssues: string[] = [];

    // Start at homepage
    await page.goto('http://localhost:3001');
    await page.waitForTimeout(2000);

    // Test navigation links
    const navLinks = [
      { text: 'Tasks', expectedUrl: '/tasks' },
      { text: 'Agents', expectedUrl: '/agents' },
      { text: 'Communications', expectedUrl: '/communications' },
      { text: 'Analytics', expectedUrl: '/analytics' },
      { text: 'Health', expectedUrl: '/health' }
    ];

    for (const link of navLinks) {
      try {
        // Try to find and click the navigation link
        const navLink = page.locator(`nav a:has-text("${link.text}"), nav button:has-text("${link.text}")`);
        const count = await navLink.count();
        
        if (count === 0) {
          navigationIssues.push(`Navigation link for "${link.text}" not found`);
          continue;
        }

        await navLink.first().click();
        await page.waitForTimeout(1000);

        const currentUrl = page.url();
        if (!currentUrl.includes(link.expectedUrl)) {
          navigationIssues.push(`Navigation to ${link.text} failed - expected ${link.expectedUrl}, got ${currentUrl}`);
        }
      } catch (error) {
        navigationIssues.push(`Navigation test for ${link.text} failed: ${error}`);
      }
    }

    console.log(`Navigation issues found: ${navigationIssues.length}`);
    if (navigationIssues.length > 0) {
      console.log('Issues:', navigationIssues);
    }
  });

  test('Test Responsive Design', async ({ page }) => {
    console.log('\n🔍 Testing responsive design...');
    const responsiveIssues: string[] = [];

    const viewports = [
      { name: 'Mobile', width: 375, height: 667 },
      { name: 'Tablet', width: 768, height: 1024 },
      { name: 'Desktop', width: 1200, height: 800 }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('http://localhost:3001');
      await page.waitForTimeout(2000);

      // Check if content is visible and not overflowing
      const overflow = await page.evaluate(() => {
        const body = document.body;
        return body.scrollWidth > body.clientWidth || body.scrollHeight > window.innerHeight * 2;
      });

      if (overflow) {
        responsiveIssues.push(`Content overflow detected at ${viewport.name} (${viewport.width}x${viewport.height})`);
      }

      // Take screenshot for each viewport
      await page.screenshot({ 
        path: join(resultsDir, `responsive-${viewport.name.toLowerCase()}.png`),
        fullPage: true 
      });
    }

    console.log(`Responsive issues found: ${responsiveIssues.length}`);
    if (responsiveIssues.length > 0) {
      console.log('Issues:', responsiveIssues);
    }
  });

  test.afterAll(async () => {
    // Generate comprehensive report
    console.log('\n📋 COMPREHENSIVE TEST REPORT\n');
    console.log('=' .repeat(80));

    let totalErrors = 0;
    let totalWarnings = 0;
    let totalUIIssues = 0;
    let totalAPIFailures = 0;

    for (const result of results) {
      console.log(`\n📄 ${result.page} (${result.url})`);
      console.log('-'.repeat(40));
      
      console.log(`⏱️  Load time: ${result.loadTime}ms`);
      console.log(`📸 Screenshot: ${result.screenshot}`);
      
      if (result.consoleErrors.length > 0) {
        console.log(`\n❌ Console Errors (${result.consoleErrors.length}):`);
        result.consoleErrors.forEach((err, i) => {
          if (i < 5) console.log(`   ${i + 1}. ${err.substring(0, 200)}`);
        });
        if (result.consoleErrors.length > 5) {
          console.log(`   ... and ${result.consoleErrors.length - 5} more`);
        }
        totalErrors += result.consoleErrors.length;
      }

      if (result.reactErrors.length > 0) {
        console.log(`\n⚛️  React Errors (${result.reactErrors.length}):`);
        result.reactErrors.forEach((err, i) => {
          if (i < 3) console.log(`   ${i + 1}. ${err.substring(0, 200)}`);
        });
      }

      if (result.consoleWarnings.length > 0) {
        console.log(`\n⚠️  Console Warnings (${result.consoleWarnings.length}):`);
        result.consoleWarnings.forEach((warn, i) => {
          if (i < 3) console.log(`   ${i + 1}. ${warn.substring(0, 200)}`);
        });
        totalWarnings += result.consoleWarnings.length;
      }

      if (result.networkErrors.length > 0) {
        console.log(`\n🌐 Network Errors (${result.networkErrors.length}):`);
        result.networkErrors.forEach((err, i) => {
          if (i < 3) console.log(`   ${i + 1}. ${err}`);
        });
      }

      if (result.uiIssues.length > 0) {
        console.log(`\n🖼️  UI Issues (${result.uiIssues.length}):`);
        result.uiIssues.forEach((issue, i) => {
          console.log(`   ${i + 1}. ${issue}`);
        });
        totalUIIssues += result.uiIssues.length;
      }

      if (result.apiCalls.length > 0) {
        console.log(`\n📡 API Calls (${result.apiCalls.length}):`);
        const failedCalls = result.apiCalls.filter(call => call.status >= 400);
        const successfulCalls = result.apiCalls.filter(call => call.status < 400);
        
        console.log(`   ✅ Successful: ${successfulCalls.length}`);
        console.log(`   ❌ Failed: ${failedCalls.length}`);
        
        if (failedCalls.length > 0) {
          console.log(`   Failed calls:`);
          failedCalls.forEach((call, i) => {
            if (i < 5) console.log(`     - ${call.method} ${call.url} (${call.status})`);
          });
          totalAPIFailures += failedCalls.length;
        }
      }
    }

    console.log('\n' + '='.repeat(80));
    console.log('📊 SUMMARY');
    console.log('='.repeat(80));
    console.log(`Total Console Errors: ${totalErrors}`);
    console.log(`Total Console Warnings: ${totalWarnings}`);
    console.log(`Total UI Issues: ${totalUIIssues}`);
    console.log(`Total API Failures: ${totalAPIFailures}`);
    console.log(`Total Pages Tested: ${results.length}`);

    // Save detailed report to file
    const reportPath = join(resultsDir, 'comprehensive-test-report.json');
    writeFileSync(reportPath, JSON.stringify(results, null, 2));
    console.log(`\n📄 Detailed report saved to: ${reportPath}`);

    // Identify critical issues
    console.log('\n🚨 CRITICAL ISSUES:');
    const criticalIssues = results.filter(r => 
      r.reactErrors.length > 0 || 
      r.networkErrors.length > 0 || 
      r.consoleErrors.some(e => e.includes('Cannot read') || e.includes('undefined'))
    );

    if (criticalIssues.length > 0) {
      criticalIssues.forEach(issue => {
        console.log(`\n❗ ${issue.page}:`);
        if (issue.reactErrors.length > 0) {
          console.log(`   - ${issue.reactErrors.length} React errors`);
        }
        if (issue.networkErrors.length > 0) {
          console.log(`   - ${issue.networkErrors.length} network failures`);
        }
      });
    } else {
      console.log('   ✅ No critical issues found!');
    }
  });
});