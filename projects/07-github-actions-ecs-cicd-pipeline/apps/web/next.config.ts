import type { NextConfig } from "next";

// Cache Components stay off. The page has to read APP_VERSION on each request.
// create-next-app turns cacheComponents on; this app does not.
const nextConfig: NextConfig = {
  output: "standalone",
};

export default nextConfig;
