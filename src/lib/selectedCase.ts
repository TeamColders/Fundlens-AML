/** Shared selected-case context across pages (dashboard → graph / STR / audit). */

export const SELECTED_CASE_KEY = 'fundlens_selected_case';
export const ORIGIN_ACCOUNT_KEY = 'fundlens_origin_account';

export function getStoredCaseId(): string | null {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem(SELECTED_CASE_KEY);
}

export function setStoredCaseId(caseId: string): void {
  if (typeof window === 'undefined') return;
  sessionStorage.setItem(SELECTED_CASE_KEY, caseId);
}

export function getStoredOriginAccountId(): string | null {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem(ORIGIN_ACCOUNT_KEY);
}

export function setStoredOriginAccountId(accountId: string): void {
  if (typeof window === 'undefined') return;
  sessionStorage.setItem(ORIGIN_ACCOUNT_KEY, accountId);
}

export function caseQueryString(caseId: string): string {
  return `?case=${encodeURIComponent(caseId)}`;
}

export function pathWithCase(basePath: string, caseId: string): string {
  const sep = basePath.includes('?') ? '&' : '?';
  return `${basePath}${sep}case=${encodeURIComponent(caseId)}`;
}
