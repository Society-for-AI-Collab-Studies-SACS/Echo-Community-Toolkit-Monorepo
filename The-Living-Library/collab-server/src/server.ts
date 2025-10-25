import { serve } from '@hono/node-server';
import { Hono } from 'hono';
import type { Server as HttpServer } from 'http';
import pg from 'pg';
import { createClient } from 'redis';
import { WebSocket, WebSocketServer } from 'ws';
import { z } from 'zod';

const { Pool } = pg;

const config = {
  port: Number.parseInt(process.env.PORT ?? '8080', 10),
  redis: {
    host: process.env.REDIS_HOST ?? 'localhost',
    port: Number.parseInt(process.env.REDIS_PORT ?? '6379', 10),
  },
  postgres: {
    host: process.env.POSTGRES_HOST ?? 'localhost',
    port: Number.parseInt(process.env.POSTGRES_PORT ?? '5432', 10),
    database: process.env.POSTGRES_DB ?? 'vesselos_collab',
    user: process.env.POSTGRES_USER ?? 'vesselos',
    password: process.env.POSTGRES_PASSWORD ?? 'password',
  },
};

const redisClient = createClient({
  socket: {
    host: config.redis.host,
    port: config.redis.port,
  },
});

const redisPub = redisClient.duplicate();
const redisSub = redisClient.duplicate();

const pool = new Pool(config.postgres);

type NodeServer = ReturnType<typeof serve>;

interface Client {
  id: string;
  userId: string;
  workspaceId: string;
  ws: WebSocket;
  lastHeartbeat: Date;
}

const clients = new Map<string, Client>();

const MessageSchema = z.discriminatedUnion('type', [
  z.object({ type: z.literal('ping') }),
  z.object({
    type: z.literal('dictation'),
    text: z.string(),
    userId: z.string(),
  }),
  z.object({
    type: z.literal('agent_result'),
    agent: z.string(),
    result: z.unknown(),
  }),
  z.object({ type: z.literal('presence'), action: z.enum(['join', 'leave']) }),
]);

type ParsedMessage = z.infer<typeof MessageSchema>;

const app = new Hono();

async function initDatabase(): Promise<void> {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS collab_sessions (
      id SERIAL PRIMARY KEY,
      workspace_id TEXT NOT NULL,
      user_id TEXT NOT NULL,
      action TEXT NOT NULL,
      data JSONB,
      timestamp TIMESTAMPTZ DEFAULT NOW()
    )
  `);

  await pool.query(`
    CREATE TABLE IF NOT EXISTS presence (
      workspace_id TEXT NOT NULL,
      user_id TEXT NOT NULL,
      last_seen TIMESTAMPTZ DEFAULT NOW(),
      PRIMARY KEY (workspace_id, user_id)
    )
  `);

  await pool.query(`
    CREATE INDEX IF NOT EXISTS idx_presence_workspace
      ON presence(workspace_id, last_seen DESC)
  `);
}

app.get('/health', async (c) => {
  try {
    await pool.query('SELECT 1');
    await redisClient.ping();

    return c.json({
      status: 'healthy',
      services: {
        postgres: 'connected',
        redis: 'connected',
        websocket: 'active',
      },
      clients: clients.size,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'unknown error';
    return c.json({ status: 'unhealthy', error: message }, 503);
  }
});

app.get('/api/presence/:workspaceId', async (c) => {
  const workspaceId = c.req.param('workspaceId');
  const result = await pool.query(
    `SELECT user_id, last_seen FROM presence
     WHERE workspace_id = $1 AND last_seen > NOW() - INTERVAL '5 minutes'`,
    [workspaceId],
  );

  return c.json({
    workspace_id: workspaceId,
    active_users: result.rows.length,
    users: result.rows,
  });
});

function setupWebSocket(server: NodeServer): void {
  const wss = new WebSocketServer({
    server: server as unknown as HttpServer,
    path: '/ws',
  });

  wss.on('connection', async (ws, req) => {
    const url = new URL(req.url ?? '', `http://${req.headers.host}`);
    const userId = url.searchParams.get('userId');
    const workspaceId = url.searchParams.get('workspaceId');

    if (!userId || !workspaceId) {
      ws.close(1008, 'Missing userId or workspaceId');
      return;
    }

    const clientId = `${workspaceId}:${userId}`;
    const client: Client = {
      id: clientId,
      userId,
      workspaceId,
      ws,
      lastHeartbeat: new Date(),
    };
    clients.set(clientId, client);

    await pool.query(
      `INSERT INTO presence (workspace_id, user_id, last_seen)
       VALUES ($1, $2, NOW())
       ON CONFLICT (workspace_id, user_id) DO UPDATE SET last_seen = NOW()`,
      [workspaceId, userId],
    );

    await broadcastToWorkspace(workspaceId, {
      type: 'presence',
      action: 'join',
      userId,
      timestamp: new Date().toISOString(),
    });

    await pool.query(
      `INSERT INTO collab_sessions (workspace_id, user_id, action, data)
       VALUES ($1, $2, 'join', $3)`,
      [workspaceId, userId, JSON.stringify({ clientId })],
    );

    console.log(`Client connected: ${clientId}`);

    ws.on('message', async (raw) => {
      try {
        const message = MessageSchema.parse(
          JSON.parse(raw.toString()),
        ) as ParsedMessage;
        await handleMessage(client, message);
      } catch (error) {
        console.error('Message error:', error);
        ws.send(
          JSON.stringify({ type: 'error', error: (error as Error).message }),
        );
      }
    });

    ws.on('close', async () => {
      clients.delete(clientId);

      await broadcastToWorkspace(workspaceId, {
        type: 'presence',
        action: 'leave',
        userId,
        timestamp: new Date().toISOString(),
      });

      await pool.query(
        `INSERT INTO collab_sessions (workspace_id, user_id, action)
         VALUES ($1, $2, 'leave')`,
        [workspaceId, userId],
      );

      console.log(`Client disconnected: ${clientId}`);
    });
  });
}

async function handleMessage(
  client: Client,
  message: ParsedMessage,
): Promise<void> {
  switch (message.type) {
    case 'ping': {
      client.lastHeartbeat = new Date();
      await pool.query(
        `UPDATE presence SET last_seen = NOW()
         WHERE workspace_id = $1 AND user_id = $2`,
        [client.workspaceId, client.userId],
      );
      client.ws.send(
        JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() }),
      );
      break;
    }

    case 'dictation': {
      await broadcastToWorkspace(
        client.workspaceId,
        {
          type: 'dictation',
          text: message.text,
          userId: message.userId,
          timestamp: new Date().toISOString(),
        },
        client.id,
      );

      await redisPub.publish(
        `collab:${client.workspaceId}`,
        JSON.stringify({
          type: 'dictation',
          text: message.text,
          userId: message.userId,
        }),
      );

      await pool.query(
        `INSERT INTO collab_sessions (workspace_id, user_id, action, data)
         VALUES ($1, $2, 'dictation', $3)`,
        [
          client.workspaceId,
          client.userId,
          JSON.stringify({ text: message.text }),
        ],
      );
      break;
    }

    case 'agent_result': {
      await broadcastToWorkspace(client.workspaceId, {
        type: 'agent_result',
        agent: message.agent,
        result: message.result,
        timestamp: new Date().toISOString(),
      });
      break;
    }

    case 'presence':
      // Presence messages are internal only.
      break;
  }
}

async function broadcastToWorkspace(
  workspaceId: string,
  message: unknown,
  excludeClientId?: string,
): Promise<void> {
  const payload = JSON.stringify(message);
  for (const [clientId, client] of clients.entries()) {
    if (client.workspaceId === workspaceId && clientId !== excludeClientId) {
      if (client.ws.readyState === WebSocket.OPEN) {
        client.ws.send(payload);
      }
    }
  }
}

setInterval(() => {
  const now = Date.now();
  const timeoutMs = 30_000;
  for (const [clientId, client] of clients.entries()) {
    if (now - client.lastHeartbeat.getTime() > timeoutMs) {
      console.log(`Client timeout: ${clientId}`);
      client.ws.close(1000, 'Heartbeat timeout');
      clients.delete(clientId);
    }
  }
}, 5_000);

async function start(): Promise<void> {
  await redisClient.connect();
  await redisPub.connect();
  await redisSub.connect();
  await initDatabase();

  await redisSub.pSubscribe('collab:*', async (message, channel) => {
    const workspaceId = channel.split(':')[1];
    const data = JSON.parse(message.toString());
    await broadcastToWorkspace(workspaceId, data);
  });

  const server = serve({
    fetch: app.fetch,
    port: config.port,
  });

  setupWebSocket(server);

  console.log(`🚀 Collaboration server running on port ${config.port}`);
  console.log(`   Redis: ${config.redis.host}:${config.redis.port}`);
  console.log(`   PostgreSQL: ${config.postgres.host}:${config.postgres.port}`);
}

start().catch((error) => {
  console.error('Collaboration server failed to start:', error);
  process.exitCode = 1;
});
