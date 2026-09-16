import type { NextConfig } from "next";
import path from "path";

const isProd = process.env.NODE_ENV === "production";

const nextConfig: NextConfig = {
  // standalone output is only needed for the production/Docker build.
  // Leaving it on during `next dev` adds unnecessary overhead.
  ...(isProd ? { output: "standalone" as const } : {}),
  // Pin the workspace root so Turbopack does not walk up to D:\ looking for
  // node_modules (a stray root package-lock.json otherwise confuses inference).
  turbopack: {
    root: path.join(__dirname),
  },
  webpack: (config) => {
    config.experiments = {
      ...config.experiments,
      asyncWebAssembly: true,
      layers: true,
    };
    return config;
  },
};

export default nextConfig;