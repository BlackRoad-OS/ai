import Stripe from 'stripe';

export const PRODUCTS = {
  AI_STARTER: {
    name: 'AI Starter',
    description: 'Basic AI agent access for individuals',
    metadata: { tier: 'starter' },
    prices: {
      monthly: { amount: 2900, interval: 'month' as const },
      yearly: { amount: 29000, interval: 'year' as const },
    },
    features: ['3 AI agents', '10,000 requests/month', 'Email support'],
    limits: { agents: 3, requestsPerMonth: 10_000 },
  },
  AI_PRO: {
    name: 'AI Pro',
    description: 'Professional AI agent suite',
    metadata: { tier: 'pro' },
    prices: {
      monthly: { amount: 9900, interval: 'month' as const },
      yearly: { amount: 99000, interval: 'year' as const },
    },
    features: [
      'Unlimited AI agents',
      '100,000 requests/month',
      'Priority support',
      'Custom model fine-tuning',
    ],
    limits: { agents: -1, requestsPerMonth: 100_000 },
  },
  AI_ENTERPRISE: {
    name: 'AI Enterprise',
    description: 'Enterprise-grade AI infrastructure',
    metadata: { tier: 'enterprise' },
    prices: {
      monthly: { amount: 49900, interval: 'month' as const },
      yearly: { amount: 499000, interval: 'year' as const },
    },
    features: [
      'Unlimited everything',
      'Dedicated infrastructure',
      '99.9% SLA guarantee',
      'Custom integrations',
      'On-premise deployment option',
    ],
    limits: { agents: -1, requestsPerMonth: -1 },
  },
} as const;

export function createStripeClient(secretKey: string): Stripe {
  return new Stripe(secretKey, {
    apiVersion: '2024-12-18.acacia',
    typescript: true,
  });
}
