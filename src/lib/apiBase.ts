/** API base URL: same-origin `/api` in Docker; full URL when frontend is on Vercel etc. */
export function getApiBase(): string {
  const env = import.meta.env.VITE_API_URL as string | undefined;
  if (env && env.trim().length > 0) {
    return env.trim().replace(/\/$/, '');
  }
  return '/api';
}
