import { Hono } from 'hono';

export const stripeRoutes = new Hono();

const STRIPE_PRODUCTS = {
  'ai-starter': {
    id: 'ai-starter',
    name: 'AI Starter',
    description: 'Basic AI agent access for individuals',
    priceMonthly: 2900,
    priceYearly: 29000,
    features: ['3 AI agents', '10K requests/month', 'Email support'],
  },
  'ai-pro': {
    id: 'ai-pro',
    name: 'AI Pro',
    description: 'Professional AI agent suite',
    priceMonthly: 9900,
    priceYearly: 99000,
    features: [
      'Unlimited AI agents',
      '100K requests/month',
      'Priority support',
      'Custom models',
    ],
  },
  'ai-enterprise': {
    id: 'ai-enterprise',
    name: 'AI Enterprise',
    description: 'Enterprise-grade AI infrastructure',
    priceMonthly: 49900,
    priceYearly: 499000,
    features: [
      'Unlimited everything',
      'Dedicated infrastructure',
      'SLA guarantee',
      'Custom integrations',
      'On-premise deployment',
    ],
  },
} as const;

stripeRoutes.get('/products', (c) => {
  return c.json({ products: Object.values(STRIPE_PRODUCTS) });
});

stripeRoutes.post('/webhook', async (c) => {
  const signature = c.req.header('stripe-signature');
  if (!signature) {
    return c.json({ error: 'Missing signature' }, 400);
  }

  return c.json({ received: true });
});

stripeRoutes.post('/checkout', async (c) => {
  const body = await c.req.json();
  const productId = body.productId as keyof typeof STRIPE_PRODUCTS;

  if (!STRIPE_PRODUCTS[productId]) {
    return c.json({ error: 'Invalid product' }, 400);
  }

  return c.json({
    status: 'checkout_created',
    product: STRIPE_PRODUCTS[productId],
  });
});
