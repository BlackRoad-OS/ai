import { Hono } from 'hono';

export const healthRoutes = new Hono();

healthRoutes.get('/', (c) => {
  return c.json({
    status: 'ok',
    service: '@blackroad-os/ai',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
  });
});

healthRoutes.get('/ready', (c) => {
  return c.json({
    status: 'ready',
    checks: {
      database: 'ok',
      stripe: 'ok',
    },
  });
});
