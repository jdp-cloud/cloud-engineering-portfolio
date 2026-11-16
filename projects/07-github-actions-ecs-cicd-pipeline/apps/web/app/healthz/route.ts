import { connection } from "next/server";
import { readRuntimeEnv } from "../../lib/runtime-env";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET() {
  await connection();
  return Response.json({
    status: "ok",
    version: readRuntimeEnv("APP_VERSION", "dev"),
  });
}
