interface GraphNodeProps {
  id: string;
  x: number; // percentage
  y: number; // percentage
  radius: number;
  label: string;
  sublabel?: string;
  amount?: string;
  timestamp?: string;
  color: 'amber' | 'red' | 'teal' | 'teal-dashed';
  glow?: boolean;
  critical?: boolean;
  onHover?: (id: string | null, x?: number, y?: number) => void;
  onClick?: (id: string) => void;
}

export default function GraphNode({
  id,
  x,
  y,
  radius,
  label,
  sublabel,
  amount,
  timestamp,
  color,
  glow,
  critical,
  onHover,
  onClick,
}: GraphNodeProps) {
  const colorMap = {
    amber: '#F59E0B',
    red: '#E31E24',
    teal: '#00C9A7',
    'teal-dashed': '#00C9A7',
  };

  const strokeColor = colorMap[color];
  const isDashed = color === 'teal-dashed';

  // Convert percentage to actual SVG coordinates
  const svgX = `${x}%`;
  const svgY = `${y}%`;

  const handleMouseEnter = (e: React.MouseEvent<SVGGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    onHover?.(id, rect.left + rect.width / 2, rect.top);
  };

  const handleMouseLeave = () => {
    onHover?.(null);
  };

  const handleClick = () => {
    onClick?.(id);
  };

  return (
    <g
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
      className="cursor-pointer transition-all duration-300"
    >
      {/* Outer glow ring (if enabled) */}
      {glow && (
        <circle
          cx={svgX}
          cy={svgY}
          r={radius + 4}
          fill="none"
          stroke={strokeColor}
          strokeWidth="2"
          opacity="0"
          className="animate-pulse"
          style={{
            filter: color === 'red' ? 'url(#red-glow-g), url(#red-glow)' : 'url(#amber-glow-g), url(#amber-glow)',
            animation: 'pulse-glow 2s ease-in-out infinite',
          }}
        />
      )}

      {/* Main node circle */}
      <circle
        cx={svgX}
        cy={svgY}
        r={radius}
        fill="white"
        stroke={strokeColor}
        strokeWidth="3"
        strokeDasharray={isDashed ? '5 5' : 'none'}
        className="transition-all duration-300 hover:brightness-95"
        style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))' }}
      />

      {/* Label text */}
      <text
        x={svgX}
        y={svgY}
        textAnchor="middle"
        dy={sublabel ? "-0.3em" : "0.35em"}
        fill="#1a1a1a"
        fontSize="10"
        fontFamily="DM Mono"
        fontWeight="bold"
        className="pointer-events-none select-none"
      >
        {label}
      </text>

      {/* Sublabel only */}
      {sublabel && (
        <text
          x={svgX}
          y={svgY}
          textAnchor="middle"
          dy="0.9em"
          fill={strokeColor}
          fontSize="9"
          fontFamily="DM Mono"
          fontWeight="600"
          className="pointer-events-none select-none"
        >
          {sublabel}
        </text>
      )}

      {/* Timestamp */}
      {timestamp && (
        <text
          x={svgX}
          y={svgY}
          textAnchor="middle"
          dy="1.8em"
          fill="#666666"
          fontSize="8"
          fontFamily="DM Mono"
          className="pointer-events-none select-none"
        >
          {timestamp}
        </text>
      )}

      <style>{`
        @keyframes pulse-glow {
          0%, 100% {
            opacity: 0.4;
            transform: scale(1);
          }
          50% {
            opacity: 0.8;
            transform: scale(1.05);
          }
        }
      `}</style>
    </g>
  );
}