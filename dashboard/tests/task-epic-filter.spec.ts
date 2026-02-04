import { test, expect } from '@playwright/test';

test('task epic filter lists epics and filters tasks', async ({ page }) => {
  await page.route('**/api/v1/epics**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 1,
          name: 'Authentication',
          description: 'Auth flows',
          created_at: '2026-02-01T00:00:00Z',
          task_count: 0,
          completed_task_count: 0,
          in_progress_task_count: 0,
        },
        {
          id: 2,
          name: 'Payments',
          description: 'Payment system',
          created_at: '2026-02-01T00:00:00Z',
          task_count: 0,
          completed_task_count: 0,
          in_progress_task_count: 0,
        },
      ]),
    });
  });

  // Keep the rest of the Task Management page happy without requiring a real API.
  await page.route('**/api/v1/tasks**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 11,
          feature_id: 101,
          epic_id: 1,
          title: 'Auth task',
          description: 'Auth task description',
          created_by: 'test_agent',
          target_role: 'backend_dev',
          difficulty: 'senior',
          complexity: 'minor',
          branch: 'main',
          status: 'created',
          locked_by: null,
          locked_at: null,
          notes: null,
          created_at: '2026-02-01T00:00:00Z',
          updated_at: '2026-02-01T00:00:00Z',
        },
        {
          id: 22,
          feature_id: 202,
          epic_id: 2,
          title: 'Payments task',
          description: 'Payments task description',
          created_by: 'test_agent',
          target_role: 'backend_dev',
          difficulty: 'senior',
          complexity: 'minor',
          branch: 'main',
          status: 'created',
          locked_by: null,
          locked_at: null,
          notes: null,
          created_at: '2026-02-01T00:00:00Z',
          updated_at: '2026-02-01T00:00:00Z',
        },
      ]),
    });
  });
  await page.route('**/api/v1/agents**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });

  await page.goto('/tasks');

  await page.locator('#epic-filter').click();

  await expect(page.getByRole('option', { name: 'Authentication' })).toBeVisible();
  await expect(page.getByRole('option', { name: 'Payments' })).toBeVisible();

  await page.getByRole('option', { name: 'Authentication' }).click();

  await expect(page.getByText('Auth task')).toBeVisible();
  await expect(page.getByText('Payments task')).not.toBeVisible();
});
