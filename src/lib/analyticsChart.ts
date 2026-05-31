import type { DailyTrend } from '../api/types';

export function trendMaxValue(trend: DailyTrend[]): number {
  if (!trend.length) return 1;
  return Math.max(1, ...trend.map((d) => Math.max(d.alerts, d.confirmed ?? 0)));
}

/** Build SVG polyline points in 0–100 coordinate space. */
export function buildTrendPolyline(
  trend: DailyTrend[],
  field: 'alerts' | 'confirmed',
  maxVal: number,
): string {
  if (!trend.length) return '';
  const h = 100;
  const w = 100;
  const step = trend.length > 1 ? w / (trend.length - 1) : 0;

  return trend
    .map((d, i) => {
      const val = field === 'alerts' ? d.alerts : d.confirmed ?? 0;
      const x = trend.length > 1 ? i * step : w / 2;
      const y = h - (val / maxVal) * (h - 8) - 4;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
}

export function buildTrendArea(
  trend: DailyTrend[],
  field: 'alerts' | 'confirmed',
  maxVal: number,
): string {
  const line = buildTrendPolyline(trend, field, maxVal);
  if (!line) return '';
  const firstX = line.split(' ')[0]?.split(',')[0] ?? '0';
  const last = line.split(' ').pop() ?? '100,100';
  const lastX = last.split(',')[0];
  return `${line} ${lastX},100 ${firstX},100`;
}

export function formatCr(amount: number): string {
  if (amount >= 10_000_000) return `₹${(amount / 10_000_000).toFixed(1)} Cr`;
  if (amount >= 100_000) return `₹${(amount / 100_000).toFixed(1)} L`;
  return `₹${Math.round(amount).toLocaleString('en-IN')}`;
}
