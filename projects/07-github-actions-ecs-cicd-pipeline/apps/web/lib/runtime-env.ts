// Read at request time. Bracket access so Next does not inline the value
// during `next build`. The task definition sets APP_VERSION on the container.
export function readRuntimeEnv(name: string, fallback: string): string {
  const value = process.env[name];
  if (typeof value === "string" && value.length > 0) {
    return value;
  }
  return fallback;
}
