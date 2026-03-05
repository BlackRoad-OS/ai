import { describe, it, expect } from 'vitest';
import { app } from '../index.js';

describe('Health Routes', () => {
  it('GET /health returns status ok', async () => {
    const res = await app.request('/health');
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.status).toBe('ok');
    expect(body.service).toBe('@blackroad-os/ai');
    expect(body.version).toBe('1.0.0');
    expect(body.timestamp).toBeDefined();
  });

  it('GET /health/ready returns readiness status', async () => {
    const res = await app.request('/health/ready');
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.status).toBe('ready');
    expect(body.checks).toBeDefined();
  });
});

describe('Agent Routes', () => {
  it('GET /api/agents returns agent list', async () => {
    const res = await app.request('/api/agents');
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.agents).toHaveLength(3);
    expect(body.agents[0].id).toBe('reasoning');
  });

  it('POST /api/agents/invoke validates input', async () => {
    const res = await app.request('/api/agents/invoke', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: '' }),
    });
    expect(res.status).toBe(400);
  });

  it('POST /api/agents/invoke accepts valid input', async () => {
    const res = await app.request('/api/agents/invoke', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: 'Hello, analyze this.' }),
    });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.status).toBe('queued');
  });
});

describe('Stripe Routes', () => {
  it('GET /api/stripe/products returns products', async () => {
    const res = await app.request('/api/stripe/products');
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.products).toHaveLength(3);
    expect(body.products[0].id).toBe('ai-starter');
  });

  it('POST /api/stripe/webhook requires signature', async () => {
    const res = await app.request('/api/stripe/webhook', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    expect(res.status).toBe(400);
  });
});

describe('404 handler', () => {
  it('returns 404 for unknown routes', async () => {
    const res = await app.request('/nonexistent');
    expect(res.status).toBe(404);
    const body = await res.json();
    expect(body.error).toBe('Not found');
  });
});
