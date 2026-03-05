import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { agentRoutes } from './routes/agents.js';
import { healthRoutes } from './routes/health.js';
import { stripeRoutes } from './routes/stripe.js';

const app = new Hono();

app.use('*', logger());
app.use(
  '*',
  cors({
    origin: ['https://blackroad.io', 'https://app.blackroad.io'],
    allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowHeaders: ['Content-Type', 'Authorization', 'X-API-Key'],
    maxAge: 86400,
  }),
);

app.route('/health', healthRoutes);
app.route('/api/agents', agentRoutes);
app.route('/api/stripe', stripeRoutes);

app.notFound((c) => c.json({ error: 'Not found' }, 404));

app.onError((err, c) => {
  console.error(`[error] ${err.message}`);
  return c.json({ error: 'Internal server error' }, 500);
});

export default app;
export { app };
