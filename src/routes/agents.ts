import { Hono } from 'hono';
import { z } from 'zod';

const AgentRequestSchema = z.object({
  model: z.string().default('claude-sonnet-4-20250514'),
  prompt: z.string().min(1).max(100_000),
  maxTokens: z.number().int().min(1).max(8192).default(4096),
  temperature: z.number().min(0).max(1).default(0.7),
});

export const agentRoutes = new Hono();

agentRoutes.get('/', (c) => {
  return c.json({
    agents: [
      {
        id: 'reasoning',
        name: 'Reasoning Agent',
        description: 'Advanced reasoning and analysis',
        model: 'claude-sonnet-4-20250514',
      },
      {
        id: 'code',
        name: 'Code Agent',
        description: 'Code generation and review',
        model: 'claude-sonnet-4-20250514',
      },
      {
        id: 'research',
        name: 'Research Agent',
        description: 'Deep research and information synthesis',
        model: 'claude-sonnet-4-20250514',
      },
    ],
  });
});

agentRoutes.post('/invoke', async (c) => {
  const body = await c.req.json();
  const parsed = AgentRequestSchema.safeParse(body);

  if (!parsed.success) {
    return c.json({ error: 'Invalid request', details: parsed.error.flatten() }, 400);
  }

  return c.json({
    status: 'queued',
    message: 'Agent invocation queued for processing',
    request: parsed.data,
  });
});
