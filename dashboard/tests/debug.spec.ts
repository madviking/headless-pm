import { test, expect } from '@playwright/test';

test('debug what is on the page', async ({ page }) => {
  await page.goto('http://localhost:3001');
  
  // Take a screenshot to see what we're working with
  await page.screenshot({ path: 'tests/screenshots/debug-homepage.png', fullPage: true });
  
  // Log all the text content on the page
  const pageText = await page.textContent('body');
  console.log('Page text content:', pageText);
  
  // Log all links on the page
  const links = await page.locator('a').all();
  console.log('Number of links found:', links.length);
  
  for (let i = 0; i < links.length; i++) {
    const link = links[i];
    const text = await link.textContent();
    const href = await link.getAttribute('href');
    console.log(`Link ${i}: text="${text}", href="${href}"`);
  }
  
  // Check if navigation exists
  const nav = await page.locator('nav').count();
  console.log('Number of nav elements:', nav);
  
  // Check for any visible buttons
  const buttons = await page.locator('button').all();
  console.log('Number of buttons found:', buttons.length);
  
  for (let i = 0; i < Math.min(buttons.length, 10); i++) {
    const button = buttons[i];
    const text = await button.textContent();
    const visible = await button.isVisible();
    console.log(`Button ${i}: text="${text}", visible=${visible}`);
  }
});