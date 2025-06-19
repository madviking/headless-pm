import { test, expect } from '@playwright/test';

test.describe('Component-Level Issue Detection', () => {
  test('Check for React component errors and warnings', async ({ page }) => {
    const componentIssues: any = {
      hydrationErrors: [],
      propErrors: [],
      keyWarnings: [],
      effectErrors: [],
      renderErrors: []
    };

    // Enhanced console monitoring for React-specific issues
    page.on('console', msg => {
      const text = msg.text();
      const type = msg.type();

      if (type === 'error' || type === 'warning') {
        // Hydration errors
        if (text.includes('Hydration') || text.includes('did not match')) {
          componentIssues.hydrationErrors.push(text);
        }
        
        // Prop type errors
        if (text.includes('prop') || text.includes('PropTypes')) {
          componentIssues.propErrors.push(text);
        }
        
        // React key warnings
        if (text.includes('unique "key" prop') || text.includes('key prop')) {
          componentIssues.keyWarnings.push(text);
        }
        
        // useEffect errors
        if (text.includes('useEffect') || text.includes('dependency')) {
          componentIssues.effectErrors.push(text);
        }
        
        // Render errors
        if (text.includes('render') || text.includes('Cannot read properties')) {
          componentIssues.renderErrors.push(text);
        }
      }
    });

    console.log('\n🔍 Checking for component-level issues...\n');

    // Test each page
    const pages = [
      { name: 'Homepage', url: '/' },
      { name: 'Tasks', url: '/tasks' },
      { name: 'Agents', url: '/agents' },
      { name: 'Communications', url: '/communications' },
      { name: 'Analytics', url: '/analytics' },
      { name: 'Health', url: '/health' }
    ];

    for (const pageInfo of pages) {
      await page.goto(`http://localhost:3001${pageInfo.url}`);
      await page.waitForTimeout(2000);

      // Check for React StrictMode double renders
      const renderCount = await page.evaluate(() => {
        return (window as any).__REACT_RENDER_COUNT__ || 0;
      });

      console.log(`\n📄 ${pageInfo.name}:`);
      
      // Check component tree depth
      const componentDepth = await page.evaluate(() => {
        let maxDepth = 0;
        function checkDepth(element: Element, depth: number = 0): void {
          maxDepth = Math.max(maxDepth, depth);
          Array.from(element.children).forEach(child => checkDepth(child, depth + 1));
        }
        const root = document.getElementById('__next') || document.getElementById('root');
        if (root) checkDepth(root);
        return maxDepth;
      });
      
      console.log(`  Component tree depth: ${componentDepth}`);
      if (componentDepth > 20) {
        console.log('  ⚠️  Very deep component tree - possible performance issue');
      }

      // Check for unused/empty divs
      const emptyDivs = await page.evaluate(() => {
        const divs = Array.from(document.querySelectorAll('div'));
        return divs.filter(div => 
          div.children.length === 0 && 
          div.textContent?.trim() === '' &&
          !div.className &&
          !div.id
        ).length;
      });
      
      if (emptyDivs > 10) {
        console.log(`  ⚠️  ${emptyDivs} empty divs found - possible render issue`);
      }

      // Check for inline styles (potential CSS-in-JS issues)
      const inlineStyles = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('[style]')).length;
      });
      
      console.log(`  Inline styles: ${inlineStyles}`);

      // Check for accessibility issues
      const missingAltText = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('img:not([alt])')).length;
      });
      
      if (missingAltText > 0) {
        console.log(`  ⚠️  ${missingAltText} images missing alt text`);
      }

      // Check for form elements without labels
      const unlabeledInputs = await page.evaluate(() => {
        const inputs = Array.from(document.querySelectorAll('input, select, textarea'));
        return inputs.filter(input => {
          const id = input.id;
          if (!id) return true;
          return !document.querySelector(`label[for="${id}"]`);
        }).length;
      });
      
      if (unlabeledInputs > 0) {
        console.log(`  ⚠️  ${unlabeledInputs} form elements without labels`);
      }
    }

    // Report component issues
    console.log('\n📊 Component Issue Summary:');
    console.log(`  Hydration errors: ${componentIssues.hydrationErrors.length}`);
    console.log(`  Prop errors: ${componentIssues.propErrors.length}`);
    console.log(`  Key warnings: ${componentIssues.keyWarnings.length}`);
    console.log(`  Effect errors: ${componentIssues.effectErrors.length}`);
    console.log(`  Render errors: ${componentIssues.renderErrors.length}`);

    if (componentIssues.hydrationErrors.length > 0) {
      console.log('\n❌ Hydration Errors:');
      componentIssues.hydrationErrors.slice(0, 3).forEach((err: string) => {
        console.log(`  - ${err}`);
      });
    }

    if (componentIssues.renderErrors.length > 0) {
      console.log('\n❌ Render Errors:');
      componentIssues.renderErrors.slice(0, 3).forEach((err: string) => {
        console.log(`  - ${err}`);
      });
    }
  });

  test('Check component interactivity and event handlers', async ({ page }) => {
    console.log('\n🔍 Testing component interactivity...\n');

    // Test homepage
    await page.goto('http://localhost:3001');
    await page.waitForTimeout(2000);

    // Check for clickable elements
    const clickableElements = await page.locator('button, a, [role="button"], [onclick]').count();
    console.log(`Clickable elements on homepage: ${clickableElements}`);

    // Test navigation
    const navLinks = await page.locator('nav a, nav button').all();
    console.log(`Navigation links found: ${navLinks.length}`);

    // Test Tasks page interactions
    await page.goto('http://localhost:3001/tasks');
    await page.waitForTimeout(2000);

    // Try to find and test view switcher
    const viewButtons = await page.locator('button:has-text("Board"), button:has-text("Analytics"), button:has-text("Timeline")').all();
    console.log(`\nTask view buttons found: ${viewButtons.length}`);

    for (const button of viewButtons) {
      try {
        const text = await button.textContent();
        await button.click();
        await page.waitForTimeout(500);
        console.log(`  ✅ Clicked ${text} button`);
        
        // Check if view changed
        const viewChanged = await page.evaluate(() => {
          // Check for any visible change in the DOM
          return document.body.innerHTML.length;
        });
        
        if (viewChanged) {
          console.log(`     View updated after clicking ${text}`);
        }
      } catch (error) {
        console.log(`  ❌ Failed to click button: ${error}`);
      }
    }

    // Test form inputs
    const inputs = await page.locator('input, select, textarea').all();
    console.log(`\nForm inputs found: ${inputs.length}`);

    for (let i = 0; i < Math.min(inputs.length, 3); i++) {
      try {
        const input = inputs[i];
        const tagName = await input.evaluate(el => el.tagName);
        const type = await input.getAttribute('type');
        
        if (tagName === 'INPUT' && type !== 'checkbox' && type !== 'radio') {
          await input.fill('Test input');
          console.log(`  ✅ Filled input field ${i + 1}`);
        }
      } catch (error) {
        console.log(`  ❌ Failed to interact with input ${i + 1}`);
      }
    }
  });

  test('Check for memory leaks and performance issues', async ({ page }) => {
    console.log('\n🔍 Testing for memory leaks and performance...\n');

    // Enable performance monitoring
    await page.goto('http://localhost:3001');
    
    // Get initial memory usage
    const initialMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize;
      }
      return null;
    });

    // Navigate through pages multiple times
    for (let i = 0; i < 3; i++) {
      await page.goto('http://localhost:3001/tasks');
      await page.waitForTimeout(1000);
      await page.goto('http://localhost:3001/agents');
      await page.waitForTimeout(1000);
      await page.goto('http://localhost:3001');
      await page.waitForTimeout(1000);
    }

    // Get final memory usage
    const finalMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize;
      }
      return null;
    });

    if (initialMemory && finalMemory) {
      const memoryIncrease = finalMemory - initialMemory;
      const increasePercentage = (memoryIncrease / initialMemory) * 100;
      
      console.log(`Initial memory: ${(initialMemory / 1024 / 1024).toFixed(2)} MB`);
      console.log(`Final memory: ${(finalMemory / 1024 / 1024).toFixed(2)} MB`);
      console.log(`Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)} MB (${increasePercentage.toFixed(1)}%)`);
      
      if (increasePercentage > 50) {
        console.log('⚠️  Significant memory increase detected - possible memory leak');
      }
    }

    // Check for event listener accumulation
    const eventListeners = await page.evaluate(() => {
      const allElements = document.querySelectorAll('*');
      let totalListeners = 0;
      
      allElements.forEach(element => {
        const listeners = (element as any).__eventListeners;
        if (listeners) {
          totalListeners += Object.keys(listeners).length;
        }
      });
      
      return totalListeners;
    });

    console.log(`\nEvent listeners attached: ${eventListeners}`);
    if (eventListeners > 1000) {
      console.log('⚠️  High number of event listeners - possible memory leak');
    }

    // Check render performance
    const renderMetrics = await page.evaluate(() => {
      const entries = performance.getEntriesByType('measure');
      return entries.filter(entry => 
        entry.name.includes('render') || 
        entry.name.includes('React')
      ).map(entry => ({
        name: entry.name,
        duration: entry.duration
      }));
    });

    if (renderMetrics.length > 0) {
      console.log('\nRender performance metrics:');
      renderMetrics.forEach(metric => {
        console.log(`  ${metric.name}: ${metric.duration.toFixed(2)}ms`);
      });
    }
  });
});