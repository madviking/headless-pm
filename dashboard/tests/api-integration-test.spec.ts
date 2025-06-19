import { test, expect } from '@playwright/test';

test.describe('API Integration and Data Flow Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Monitor all API calls
    const apiCalls: any[] = [];
    
    page.on('request', request => {
      if (request.url().includes('/api/') || request.url().includes('localhost:6969')) {
        apiCalls.push({
          url: request.url(),
          method: request.method(),
          postData: request.postData(),
          headers: request.headers(),
          timestamp: Date.now()
        });
      }
    });

    page.on('response', response => {
      if (response.url().includes('/api/') || response.url().includes('localhost:6969')) {
        const callIndex = apiCalls.findIndex(call => 
          call.url === response.url() && 
          call.method === response.request().method()
        );
        
        if (callIndex >= 0) {
          apiCalls[callIndex].status = response.status();
          apiCalls[callIndex].statusText = response.statusText();
          response.text().then(body => {
            apiCalls[callIndex].responseBody = body;
          }).catch(() => {
            apiCalls[callIndex].responseBody = 'Could not read body';
          });
        }
      }
    });

    (page as any).apiCalls = apiCalls;
  });

  test('Check API connectivity and data fetching', async ({ page }) => {
    const apiCalls = (page as any).apiCalls;
    
    console.log('\n🔍 Testing API connectivity...\n');

    // Test homepage - should fetch epics
    await page.goto('http://localhost:3001');
    await page.waitForTimeout(3000);

    const epicCalls = apiCalls.filter((call: any) => call.url.includes('/epics'));
    console.log(`📊 Epic API calls: ${epicCalls.length}`);
    if (epicCalls.length > 0) {
      epicCalls.forEach((call: any) => {
        console.log(`  - ${call.method} ${call.url} -> ${call.status || 'pending'}`);
        if (call.responseBody) {
          try {
            const data = JSON.parse(call.responseBody);
            console.log(`    Response: ${Array.isArray(data) ? `${data.length} epics` : 'single epic'}`);
          } catch {
            console.log(`    Response: ${call.responseBody.substring(0, 100)}...`);
          }
        }
      });
    } else {
      console.log('  ❌ No epic API calls detected');
    }

    // Test tasks page - should fetch tasks
    await page.goto('http://localhost:3001/tasks');
    await page.waitForTimeout(3000);

    const taskCalls = apiCalls.filter((call: any) => call.url.includes('/tasks'));
    console.log(`\n📊 Task API calls: ${taskCalls.length}`);
    if (taskCalls.length > 0) {
      taskCalls.forEach((call: any) => {
        console.log(`  - ${call.method} ${call.url} -> ${call.status || 'pending'}`);
      });
    } else {
      console.log('  ❌ No task API calls detected');
    }

    // Test agents page - should fetch agents
    await page.goto('http://localhost:3001/agents');
    await page.waitForTimeout(3000);

    const agentCalls = apiCalls.filter((call: any) => call.url.includes('/agents'));
    console.log(`\n📊 Agent API calls: ${agentCalls.length}`);
    if (agentCalls.length > 0) {
      agentCalls.forEach((call: any) => {
        console.log(`  - ${call.method} ${call.url} -> ${call.status || 'pending'}`);
      });
    } else {
      console.log('  ❌ No agent API calls detected');
    }

    // Check for failed API calls
    const failedCalls = apiCalls.filter((call: any) => call.status && call.status >= 400);
    if (failedCalls.length > 0) {
      console.log(`\n❌ Failed API calls: ${failedCalls.length}`);
      failedCalls.forEach((call: any) => {
        console.log(`  - ${call.method} ${call.url} -> ${call.status} ${call.statusText}`);
      });
    }

    // Check for CORS issues
    const corsErrors = apiCalls.filter((call: any) => 
      call.status === 0 || 
      (call.responseBody && call.responseBody.includes('CORS'))
    );
    if (corsErrors.length > 0) {
      console.log(`\n⚠️  Potential CORS issues: ${corsErrors.length}`);
    }

    // Summary
    console.log('\n📋 API Integration Summary:');
    console.log(`  Total API calls: ${apiCalls.length}`);
    console.log(`  Successful calls: ${apiCalls.filter((c: any) => c.status && c.status < 400).length}`);
    console.log(`  Failed calls: ${failedCalls.length}`);
    console.log(`  Pending/No response: ${apiCalls.filter((c: any) => !c.status).length}`);
  });

  test('Check real-time updates and WebSocket connections', async ({ page }) => {
    console.log('\n🔍 Testing real-time features...\n');

    const wsConnections: any[] = [];
    
    // Monitor WebSocket connections
    page.on('websocket', ws => {
      console.log('WebSocket created:', ws.url());
      wsConnections.push({
        url: ws.url(),
        created: Date.now()
      });

      ws.on('framereceived', event => {
        console.log('WebSocket message received:', event.payload);
      });

      ws.on('framesent', event => {
        console.log('WebSocket message sent:', event.payload);
      });

      ws.on('close', () => {
        console.log('WebSocket closed:', ws.url());
      });
    });

    await page.goto('http://localhost:3001/agents');
    await page.waitForTimeout(5000);

    console.log(`WebSocket connections: ${wsConnections.length}`);
    if (wsConnections.length === 0) {
      console.log('ℹ️  No WebSocket connections detected (may be using polling instead)');
    }
  });

  test('Check error handling and loading states', async ({ page }) => {
    console.log('\n🔍 Testing error handling...\n');

    // Intercept API calls to simulate errors
    await page.route('**/api/v1/epics', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' })
      });
    });

    await page.goto('http://localhost:3001');
    await page.waitForTimeout(3000);

    // Check for error UI
    const errorElements = await page.locator('text=/error|failed|retry/i').count();
    console.log(`Error UI elements found: ${errorElements}`);

    // Check for infinite loading
    const loadingElements = await page.locator('[class*="loading"], [class*="spinner"], [class*="skeleton"]').count();
    console.log(`Loading elements after error: ${loadingElements}`);

    // Reset route
    await page.unroute('**/api/v1/epics');
  });

  test('Check data rendering and state management', async ({ page }) => {
    console.log('\n🔍 Testing data rendering...\n');

    // Mock successful API responses
    await page.route('**/api/v1/epics', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            name: 'Test Epic',
            description: 'Test Description',
            status: 'active',
            progress: 50,
            feature_count: 3,
            completed_features: 1
          }
        ])
      });
    });

    await page.route('**/api/v1/agents', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'agent-1',
            name: 'Test Agent',
            role: 'backend_dev',
            skill_level: 'senior',
            status: 'active',
            last_active: new Date().toISOString()
          }
        ])
      });
    });

    // Test homepage data rendering
    await page.goto('http://localhost:3001');
    await page.waitForTimeout(2000);

    const epicCards = await page.locator('text=Test Epic').count();
    console.log(`Epic cards rendered: ${epicCards}`);

    // Test agents page data rendering
    await page.goto('http://localhost:3001/agents');
    await page.waitForTimeout(2000);

    const agentElements = await page.locator('text=Test Agent').count();
    console.log(`Agent elements rendered: ${agentElements}`);

    // Check if data persists on navigation
    await page.goto('http://localhost:3001');
    await page.waitForTimeout(1000);
    
    const epicCardsAfterNav = await page.locator('text=Test Epic').count();
    console.log(`Epic cards after navigation: ${epicCardsAfterNav}`);

    if (epicCardsAfterNav === epicCards) {
      console.log('✅ State management working - data persists');
    } else {
      console.log('⚠️  State management issue - data lost on navigation');
    }
  });
});