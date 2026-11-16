// Read at request time. The task definition (and docker run -e) set these.
// Bracket access keeps a bundler from folding the value in at build time.
export function readEnv(name: string, fallback: string): string {
  const value = process.env[name];
  if (typeof value === "string" && value.length > 0) {
    return value;
  }
  return fallback;
}
