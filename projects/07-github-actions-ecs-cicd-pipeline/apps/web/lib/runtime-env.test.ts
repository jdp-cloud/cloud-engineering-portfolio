import { afterEach, describe, expect, it } from "vitest";
import { readRuntimeEnv } from "./runtime-env";

describe("readRuntimeEnv", () => {
  afterEach(() => {
    delete process.env.APP_VERSION;
  });

  it("returns the fallback when the variable is missing or empty", () => {
    delete process.env.APP_VERSION;
    expect(readRuntimeEnv("APP_VERSION", "dev")).toBe("dev");

    process.env.APP_VERSION = "";
    expect(readRuntimeEnv("APP_VERSION", "dev")).toBe("dev");
  });

  it("returns the value set on the process", () => {
    process.env.APP_VERSION = "runtime-proof";
    expect(readRuntimeEnv("APP_VERSION", "dev")).toBe("runtime-proof");
  });
});
