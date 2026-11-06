/** Address of the API for WebSockets, which cannot go through the Next.js proxy. */
export function websocketUrl(path: string): string {
  const configured = process.env.NEXT_PUBLIC_API_WS_URL;
  if (configured) return `${configured}${path}`;

  const { protocol, hostname } = window.location;
  const scheme = protocol === "https:" ? "wss" : "ws";

  // GitHub Codespaces gives every port its own host name: <name>-3000.app.github.dev
  if (hostname.endsWith(".app.github.dev")) {
    return `${scheme}://${hostname.replace(/-\d+\.app\.github\.dev$/, "-8000.app.github.dev")}${path}`;
  }
  return `${scheme}://${hostname}:8000${path}`;
}