import {
  getStoredCaseId,
  getStoredOriginAccountId,
  pathWithCase,
} from './selectedCase';

/** Resolve dev/top nav targets from the current investigation context. */
export function resolveNavPath(routeId: string): string {
  const caseId = getStoredCaseId();

  switch (routeId) {
    case 'dashboard':
      return '/';
    case 'graph':
      return caseId ? pathWithCase('/graph', caseId) : '/graph';
    case 'str':
      return caseId ? pathWithCase('/str-generation', caseId) : '/str-generation';
    case 'entity': {
      const origin = getStoredOriginAccountId();
      return origin ? `/entity/${origin}` : '/';
    }
    case 'blockchain':
      return caseId ? pathWithCase('/blockchain', caseId) : '/blockchain';
    case 'analytics':
      return '/analytics';
    case 'query':
      return '/query';
    case 'admin':
      return '/admin';
    case 'mobile':
      return '/mobile';
    default:
      return '/';
  }
}

export function isNavRouteActive(routeId: string, pathname: string): boolean {
  if (routeId === 'entity') return pathname.startsWith('/entity/');
  const base = resolveNavPath(routeId).split('?')[0];
  return pathname === base;
}
