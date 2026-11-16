import type { Server } from "node:http";
import { createApp } from "./app.js";
import { readEnv } from "./env.js";

const port = Number(readEnv("PORT", "3001"));
const app = createApp();

const server: Server = app.listen(port, "0.0.0.0", () => {
  console.log(`api listening on ${port}`);
});

// ECS sends SIGTERM on stop. Close the listener, exit 0 when it drains,
// and force an exit if that takes longer than 10 seconds.
const forceExitMs = 10_000;
let shuttingDown = false;

function shutdown(signal: NodeJS.Signals): void {
  if (shuttingDown) {
    return;
  }
  shuttingDown = true;
  console.log(`${signal} received, closing server`);

  const timer = setTimeout(() => {
    console.error(`server did not close within ${forceExitMs}ms, forcing exit`);
    process.exit(1);
  }, forceExitMs);

  server.close((error) => {
    clearTimeout(timer);
    if (error) {
      console.error(error);
      process.exit(1);
    }
    process.exit(0);
  });
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
