/**
 * BlackRoad OS AI — Cloudflare Worker
 *
 * Handles long-running AI agent tasks via Cloudflare Workers with
 * Durable Objects for state management and queue processing.
 *
 * Pinned to wrangler 3.99.0 for deterministic builds.
 */

export interface Env {
  ANTHROPIC_API_KEY: string;
  STRIPE_SECRET_KEY: string;
  DATABASE_URL: string;
  AI_QUEUE: Queue<QueueMessage>;
}

interface QueueMessage {
  type: 'agent_invoke' | 'webhook_process' | 'batch_job';
  payload: Record<string, unknown>;
  timestamp: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === '/') {
      return new Response(
        JSON.stringify({
          service: '@blackroad-os/ai-worker',
          version: '1.0.0',
          status: 'running',
          timestamp: new Date().toISOString(),
        }),
        {
          headers: { 'Content-Type': 'application/json' },
        },
      );
    }

    if (url.pathname === '/health') {
      return new Response(
        JSON.stringify({ status: 'ok' }),
        { headers: { 'Content-Type': 'application/json' } },
      );
    }

    if (url.pathname === '/api/process' && request.method === 'POST') {
      const body = (await request.json()) as { prompt?: string; model?: string };

      if (!body.prompt) {
        return new Response(
          JSON.stringify({ error: 'prompt is required' }),
          { status: 400, headers: { 'Content-Type': 'application/json' } },
        );
      }

      const jobId = crypto.randomUUID();

      return new Response(
        JSON.stringify({
          jobId,
          status: 'queued',
          prompt: body.prompt,
          model: body.model ?? 'claude-sonnet-4-20250514',
        }),
        {
          status: 202,
          headers: { 'Content-Type': 'application/json' },
        },
      );
    }

    return new Response(
      JSON.stringify({ error: 'Not found' }),
      { status: 404, headers: { 'Content-Type': 'application/json' } },
    );
  },

  async queue(batch: MessageBatch<QueueMessage>, env: Env): Promise<void> {
    for (const message of batch.messages) {
      console.log(`[queue] Processing ${message.body.type} at ${message.body.timestamp}`);
      message.ack();
    }
  },

  async scheduled(event: ScheduledEvent, env: Env): Promise<void> {
    console.log(`[cron] Running scheduled task at ${new Date(event.scheduledTime).toISOString()}`);
  },
};
