interface FlowArrowProps {
  from: { x: number; y: number };
  to: { x: number; y: number };
  amount?: string;
  color?: 'teal' | 'red';
  curved?: boolean;
  showLabel?: boolean;
  /** Stagger overlapping labels along the edge normal */
  labelIndex?: number;
}

export default function FlowArrow({
  from,
  to,
  amount,
  color = 'teal',
  curved = false,
  showLabel = false,
  labelIndex = 0,
}: FlowArrowProps) {
  const fromX = `${from.x}%`;
  const fromY = `${from.y}%`;
  const toX = `${to.x}%`;
  const toY = `${to.y}%`;

  const strokeColor = color === 'red' ? '#EF4444' : '#00C9A7';
  const opacity = color === 'red' ? 0.75 : 0.5;
  const markerId = color === 'red' ? 'arrowhead-red' : 'arrowhead-teal';

  let pathD: string;
  let labelX: number;
  let labelY: number;

  if (curved) {
    const midX = (from.x + to.x) / 2;
    const controlY = 15;
    pathD = `M ${fromX} ${fromY} Q ${midX}% ${controlY}%, ${toX} ${toY}`;
    labelX = midX;
    labelY = controlY - 4;
  } else {
    pathD = `M ${fromX} ${fromY} L ${toX} ${toY}`;
    labelX = (from.x + to.x) / 2;
    labelY = (from.y + to.y) / 2;
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const len = Math.hypot(dx, dy) || 1;
    const nx = -dy / len;
    const ny = dx / len;
    const stagger = (labelIndex - 2) * 2.5;
    labelX += nx * stagger;
    labelY += ny * stagger - 1.5;
  }

  const displayLabel = showLabel && amount;

  return (
    <g>
      <path
        d={pathD}
        fill="none"
        stroke={strokeColor}
        strokeWidth="1.5"
        strokeDasharray="4 4"
        opacity={opacity}
        markerEnd={`url(#${markerId})`}
      />

      {displayLabel && (
        <text
          x={`${labelX}%`}
          y={`${labelY}%`}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#1F2937"
          stroke="white"
          strokeWidth={4}
          paintOrder="stroke fill"
          fontSize="10"
          fontFamily="DM Mono"
          fontWeight="600"
          className="pointer-events-none select-none"
        >
          {amount}
        </text>
      )}
    </g>
  );
}
