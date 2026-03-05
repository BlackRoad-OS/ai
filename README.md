# ai

Artificial intelligence models, agents, and intelligence layers for the BlackRoad system.

**Proprietary Software** — Copyright (c) 2024-2026 BlackRoad OS, Inc. All Rights Reserved.
See [LICENSE](LICENSE) for terms.

## Architecture

```
src/
  index.ts          — Hono API server (routes, middleware, CORS)
  routes/
    health.ts       — Health and readiness endpoints
    agents.ts       — AI agent invocation API
    stripe.ts       — Stripe products, webhooks, checkout
  lib/
    env.ts          — Environment validation (Zod)
  db/
    schema.ts       — PostgreSQL schema (Drizzle ORM)
    index.ts        — Database connection pool
  agents/
    base.ts         — Base agent class (Anthropic SDK)
  stripe/
    products.ts     — Stripe product catalog and client
workers/
  src/index.ts      — Cloudflare Worker (queues, cron, long tasks)
  wrangler.toml     — Worker configuration
```

## Quick Start

```bash
# Install dependencies
npm ci

# Copy environment variables
cp .env.example .env
# Edit .env with your keys

# Run development server
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Start production server
npm start
```

## API Endpoints

| Method | Path                  | Description                |
| ------ | --------------------- | -------------------------- |
| GET    | `/health`             | Service health check       |
| GET    | `/health/ready`       | Readiness probe            |
| GET    | `/api/agents`         | List available agents      |
| POST   | `/api/agents/invoke`  | Invoke an AI agent         |
| GET    | `/api/stripe/products`| List Stripe products       |
| POST   | `/api/stripe/webhook` | Stripe webhook receiver    |
| POST   | `/api/stripe/checkout`| Create checkout session    |

## Agent Invocation

```bash
curl -X POST https://ai-api.blackroad.io/api/agents/invoke \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "prompt": "Analyze this dataset for anomalies",
    "maxTokens": 4096,
    "temperature": 0.7
  }'
```

## Stripe Products

| Plan           | Monthly | Yearly  | Agents    | Requests/mo |
| -------------- | ------- | ------- | --------- | ----------- |
| AI Starter     | $29     | $290    | 3         | 10,000      |
| AI Pro         | $99     | $990    | Unlimited | 100,000     |
| AI Enterprise  | $499    | $4,990  | Unlimited | Unlimited   |

## Cloudflare Worker

The worker handles long-running AI tasks with queue processing and scheduled jobs.

```bash
# Development
npm run worker:dev

# Deploy to staging
cd workers && npx wrangler deploy --env staging

# Deploy to production
cd workers && npx wrangler deploy --env production
```

Worker endpoints:
- `GET /` — Worker status
- `GET /health` — Health check
- `POST /api/process` — Queue an AI processing job

## Database

PostgreSQL via Drizzle ORM. Tables: `users`, `agent_invocations`, `subscriptions`, `api_keys`.

```bash
# Generate migration
npm run db:generate

# Run migration
npm run db:migrate

# Push schema (development)
npm run db:push

# Open Drizzle Studio
npm run db:studio
```

## Deployment

### Vercel (API)
Configured via `vercel.json`. Security headers enforced on all API routes.

### Railway (API Server)
Configured via `railway.json`. Nixpacks builder with health checks.

### Cloudflare Workers (Long Tasks)
Configured via `workers/wrangler.toml`. Smart placement, queue consumers, cron triggers.

## CI/CD Workflows

| Workflow          | Trigger                    | Purpose                              |
| ----------------- | -------------------------- | ------------------------------------ |
| `ci.yml`          | Push/PR to main            | Lint, typecheck, test, build         |
| `deploy.yml`      | Push to main / manual      | Deploy to Vercel, Railway, Cloudflare|
| `security.yml`    | Push/PR to main, weekly    | CodeQL, dependency review, audit     |
| `automerge.yml`   | PR events                  | Auto-merge dependabot & labeled PRs  |
| `release.yml`     | Tag push (v*)              | Create GitHub release with changelog |
| `db-migrate.yml`  | Manual dispatch            | Run database migrations              |
| `worker-deploy.yml`| Push to workers/ / manual | Deploy Cloudflare Worker             |

All GitHub Actions are **pinned to specific commit hashes** for supply chain security.

## Security

- All dependencies pinned to exact versions
- All GitHub Actions pinned to commit SHAs
- CodeQL static analysis on every push
- TruffleHog secret scanning
- Dependency review on PRs (blocks high-severity + GPL/AGPL)
- Dependabot weekly updates with automerge for minor/patch
- NPM audit in CI pipeline
- Security headers on all API responses
- See [SECURITY.md](SECURITY.md) for vulnerability reporting

## Required Secrets

Configure these in GitHub repository settings:

| Secret                  | Service     | Description                    |
| ----------------------- | ----------- | ------------------------------ |
| `ANTHROPIC_API_KEY`     | Anthropic   | Claude API key                 |
| `STRIPE_SECRET_KEY`     | Stripe      | Stripe secret key              |
| `STRIPE_WEBHOOK_SECRET` | Stripe      | Webhook signing secret         |
| `DATABASE_URL`          | PostgreSQL  | Connection string              |
| `CLOUDFLARE_API_TOKEN`  | Cloudflare  | Workers deploy token           |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare  | Account identifier             |
| `VERCEL_TOKEN`          | Vercel      | Deployment token               |
| `VERCEL_ORG_ID`         | Vercel      | Organization ID                |
| `VERCEL_PROJECT_ID`     | Vercel      | Project ID                     |
| `RAILWAY_TOKEN`         | Railway     | Deployment token               |

## Tech Stack

- **Runtime**: Node.js 20.11.0
- **Language**: TypeScript 5.7.2
- **Framework**: Hono 4.6.14
- **AI SDK**: @anthropic-ai/sdk 0.39.0
- **Database**: PostgreSQL + Drizzle ORM 0.38.3
- **Payments**: Stripe 17.5.0
- **Workers**: Cloudflare Workers + Wrangler 3.99.0
- **Validation**: Zod 3.24.1
- **Testing**: Vitest 2.1.8
- **Linting**: ESLint 9.17.0
- **Formatting**: Prettier 3.4.2

---

Copyright (c) 2024-2026 BlackRoad OS, Inc. All Rights Reserved.
Proprietary and Confidential. See [LICENSE](LICENSE) for full terms.
