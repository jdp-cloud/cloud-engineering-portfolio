import { connection } from "next/server";
import { readRuntimeEnv } from "../lib/runtime-env";
import { HelloFromApi } from "./hello-from-api";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export default async function HomePage() {
  await connection();
  const version = readRuntimeEnv("APP_VERSION", "dev");

  return (
    <main>
      <h1>Project 07</h1>
      <p>
        Web version: <span id="web-version">{version}</span>
      </p>
      <HelloFromApi />
    </main>
  );
}
