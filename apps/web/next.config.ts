import type { NextConfig } from "next";

const isLocal = process.env.NEXT_PUBLIC_APP_MODE === "local";

// Desktop version: a static site, served by the local server itself.
const localConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  turbopack: { root: process.cwd() },
};

// Cloud version: the site forwards /api to the FastAPI server.
const cloudConfig: NextConfig = {
  turbopack: { root: process.cwd() },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.API_URL ?? "http://localhost:8000"}/:path*`,
      },
    ];
  },
};

export default isLocal ? localConfig : cloudConfig;