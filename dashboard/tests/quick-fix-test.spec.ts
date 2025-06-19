import { test, expect } from '@playwright/test';

test('Quick test after infinite loop fix', async ({ page }) => {
  const errors: string[] = [];
  
  page.on('console', msg => {
    if (msg.type() === 'error' && msg.text().includes('Maximum update depth')) {
      errors.push('Infinite loop detected');
    }
  });
  
  await page.goto('http://localhost:3001');
  
  // Wait for potential errors to appear
  await page.waitForTimeout(5000);
  
  // Check if homepage loads
  await expect(page.locator('h1:has-text("Project Overview")')).toBeVisible();
  
  // Take screenshot
  await page.screenshot({ path: 'tests/screenshots/after-fix.png', fullPage: true });
  
  console.log('Infinite loop errors detected:', errors.length);
  
  if (errors.length === 0) {
    console.log('✅ Infinite loop issue fixed!');
  } else {
    console.log('❌ Still has infinite loop issues');
  }
});