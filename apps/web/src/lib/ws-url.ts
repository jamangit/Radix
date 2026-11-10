import { isLocalMode } from "./app-mode";

/** Address of the API for WebSockets, which cannot go through the Next.js proxy. */
export function websocketUrl(path: string): string {
  const { protocol, host, hostname } = window.location;
  const scheme = protocol === "https:" ? "wss" : "ws";

  // Desktop version: the site and the API are served from the same address.
  if (isLocalMode) return `${scheme}://${host}/api${path}`;

  const configured = process.env.NEXT_PUBLIC_API_WS_URL;
  if (configured) return `${configured}${path}`;

  // GitHub Codespaces gives every port its own host name: <name>-3000.app.github.dev
  if (hostname.endsWith(".app.github.dev")) {
    return `${scheme}://${hostname.replace(/-\d+\.app\.github\.dev$/, "-8000.app.github.dev")}${path}`;
  }
  return `${scheme}://${hostname}:8000${path}`;
}