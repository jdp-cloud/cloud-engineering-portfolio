import { afterEach, describe, expect, it } from "vitest";
import request from "supertest";
import { createApp } from "./app.js";

const originalVersion = process.env.APP_VERSION;
const originalGreeting = process.env.GREETING;

function restoreEnv(): void {
  if (originalVersion === undefined) {
    delete process.env.APP_VERSION;
  } else {
    process.env.APP_VERSION = originalVersion;
  }
  if (originalGreeting === undefined) {
    delete process.env.GREETING;
  } else {
    process.env.GREETING = originalGreeting;
  }
}

describe("api routes", () => {
  afterEach(() => {
    restoreEnv();
  });

  it("GET /health and GET /api/health return the same body", async () => {
    process.env.APP_VERSION = "sha-abc123";
    const app = createApp();

    const direct = await request(app).get("/health");
    const throughApiPath = await request(app).get("/api/health");

    expect(direct.status).toBe(200);
    expect(direct.headers["x-powered-by"]).toBeUndefined();
    expect(throughApiPath.status).toBe(200);
    expect(direct.body).toEqual({ status: "ok", version: "sha-abc123" });
    expect(throughApiPath.body).toEqual(direct.body);
  });

  it("uses dev when APP_VERSION is missing or empty", async () => {
    delete process.env.APP_VERSION;
    const missing = await request(createApp()).get("/health");
    expect(missing.body).toEqual({ status: "ok", version: "dev" });

    process.env.APP_VERSION = "";
    const empty = await request(createApp()).get("/api/health");
    expect(empty.body).toEqual({ status: "ok", version: "dev" });
  });

  it("GET /api/hello returns the GREETING value", async () => {
    process.env.GREETING = "from-ssm";
    const res = await request(createApp()).get("/api/hello");
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ message: "from-ssm" });
  });

  it("uses hello when GREETING is missing", async () => {
    delete process.env.GREETING;
    const res = await request(createApp()).get("/api/hello");
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ message: "hello" });
  });
});
