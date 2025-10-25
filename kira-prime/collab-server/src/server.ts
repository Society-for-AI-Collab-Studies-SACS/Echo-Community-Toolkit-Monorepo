import express from "express";
import { createServer } from "http";
import { WebSocketServer, WebSocket } from "ws";

const PORT = process.env.PORT || "8000";
const redisUrl = process.env.COLLAB_REDIS_URL || "redis://localhost:6379/0";
const postgresDsn = process.env.COLLAB_POSTGRES_DSN ||
  "postgresql://vesselos:password@localhost:5432/vesselos_collab";

const app = express();

app.get("/health", (_req, res) => {
  res.status(200).json({ status: "ok" });
});

const server = createServer(app);
const wss = new WebSocketServer({ server, path: "/ws" });

type Event = { ts: string; message: string };
const events: Event[] = [];

wss.on("connection", (ws: WebSocket) => {
  ws.on("message", (data) => {
    const text = data.toString();
    ws.send(JSON.stringify({ echo: text }));
    events.push({ ts: new Date().toISOString(), message: text });
  });
});

server.listen(parseInt(PORT, 10), () => {
  console.log(`Collab server listening on port ${PORT}`);
  console.log(`Using Redis at ${redisUrl} and Postgres at ${postgresDsn}`);
});

