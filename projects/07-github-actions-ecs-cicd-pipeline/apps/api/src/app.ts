import express, { type Request, type Response } from "express";
import { readEnv } from "./env.js";

function health(_req: Request, res: Response): void {
  res.status(200).json({
    status: "ok",
    version: readEnv("APP_VERSION", "dev"),
  });
}

export function createApp(): express.Express {
  const app = express();
  app.disable("x-powered-by");

  // /health is for the target group. The check hits the task directly.
  // Through the ALB, /api/* is the API and every other path is web,
  // so /health on the public URL would land on web. /api/health is the
  // same body, on a path the ALB sends here.
  app.get("/health", health);
  app.get("/api/health", health);

  app.get("/api/hello", (_req: Request, res: Response) => {
    res.status(200).json({
      message: readEnv("GREETING", "hello"),
    });
  });

  return app;
}
