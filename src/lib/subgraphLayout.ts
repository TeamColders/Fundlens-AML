/**
 * Convert API subgraph + case metadata into SVG node/arrow layout for fund-flow views.
 */

export type GraphLayoutMode = 'dashboard' | 'full' | 'mini';

export interface LayoutNode {
  id: string;
  x: number;
  y: number;
  radius: number;
  label: string;
  sublabel?: string;
  color: 'amber' | 'red' | 'teal' | 'teal-dashed';
  glow?: boolean;
  critical?: boolean;
}

export interface LayoutArrow {
  id: string;
  from: { x: number; y: number };
  to: { x: number; y: number };
  amount: string;
  color?: 'teal' | 'red';
  curved?: boolean;
  showLabel?: boolean;
  labelIndex?: number;
}

export function formatAmount(amount: number): string {
  const n = Math.abs(Number(amount) || 0);
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(1)}Cr`;
  if (n >= 100000) return `₹${(n / 100000).toFixed(1)}L`;
  if (n >= 1000) return `₹${(n / 1000).toFixed(1)}K`;
  return `₹${Math.round(n).toLocaleString('en-IN')}`;
}

function getNodeStyle(node: {
  is_hub?: boolean;
  is_origin?: boolean;
  is_external?: boolean;
  risk_level?: string;
}): Pick<LayoutNode, 'color' | 'radius' | 'glow' | 'critical'> {
  if (node.is_external) return { color: 'teal', radius: 18 };
  if (node.is_hub) return { color: 'red', radius: 28, glow: true, critical: true };
  if (node.is_origin) return { color: 'amber', radius: 30, glow: true };
  if (node.risk_level === 'critical') return { color: 'red', radius: 22 };
  return { color: 'amber', radius: 20 };
}

function distributeY(count: number, index: number, top = 18, bottom = 82): number {
  if (count <= 1) return 50;
  return top + (index * (bottom - top)) / (count - 1);
}

export function subgraphToLayout(
  subgraph: { nodes?: unknown[]; edges?: unknown[] } | null | undefined,
  typology?: string,
  mode: GraphLayoutMode = 'dashboard',
): { nodes: LayoutNode[]; arrows: LayoutArrow[] } {
  if (!subgraph?.nodes?.length) {
    return { nodes: [], arrows: [] };
  }

  const compact = mode === 'dashboard' || mode === 'mini';
  const mini = mode === 'mini';
  const apiNodes = subgraph.nodes as Array<Record<string, unknown>>;
  const apiEdges = (subgraph.edges || []) as Array<Record<string, unknown>>;

  const externalNode = apiNodes.find((n) => n.id === 'EXTERNAL' || n.is_external);
  const originNode = apiNodes.find((n) => n.is_origin);
  const hubNode = apiNodes.find((n) => n.is_hub);
  const others = apiNodes.filter(
    (n) => !n.is_origin && !n.is_hub && n.id !== 'EXTERNAL' && !n.is_external,
  );

  const svgNodes: LayoutNode[] = [];
  const addNode = (
    node: Record<string, unknown>,
    x: number,
    y: number,
    extras: Partial<LayoutNode> = {},
  ) => {
    const style = getNodeStyle(node as Parameters<typeof getNodeStyle>[0]);
    const radiusScale = mini ? 0.72 : 1;
    const baseRadius = extras.radius ?? style.radius ?? 20;
    svgNodes.push({
      id: String(node.id),
      x,
      y,
      label: String(node.label || node.id),
      ...style,
      ...extras,
      radius: Math.round(baseRadius * radiusScale),
    });
  };

  if (externalNode) {
    addNode(externalNode, 8, 50, { radius: 18, sublabel: 'Inward', color: 'teal' });
  }

  if (!originNode && !hubNode && !externalNode) {
    const radius = compact ? 22 : 26;
    const baseAngle = -Math.PI / 2;
    const slice = Math.min(others.length, compact ? 8 : others.length);
    others.slice(0, slice).forEach((node, index) => {
      const angle = baseAngle + (index / slice) * 2 * Math.PI;
      addNode(
        node,
        50 + radius * Math.cos(angle),
        50 + radius * Math.sin(angle),
        { radius: compact ? 18 : 22 },
      );
    });
  } else {
    if (originNode) {
      addNode(originNode, externalNode ? 16 : 12, 50, {
        radius: compact ? 26 : 30,
        sublabel: originNode.is_dormant ? 'Dormant → Active' : 'Origin',
        color: 'amber',
        glow: true,
      });
    }

    const leftIntermediaries = others.filter((_, index) => index < Math.ceil(others.length / 2));
    const rightIntermediaries = others.filter((_, index) => index >= Math.ceil(others.length / 2));
    const nodeRadius = compact ? 18 : 22;

    leftIntermediaries.forEach((node, index) => {
      addNode(node, 32, distributeY(leftIntermediaries.length, index), { radius: nodeRadius, color: 'amber' });
    });

    if (hubNode) {
      addNode(hubNode, 50, 50, {
        radius: compact ? 26 : 30,
        sublabel: 'Hub',
        color: 'red',
        glow: true,
        critical: true,
      });
    }

    rightIntermediaries.forEach((node, index) => {
      addNode(node, 68, distributeY(rightIntermediaries.length, index), { radius: nodeRadius, color: 'amber' });
    });

    const typ = (typology || '').toLowerCase();
    if (!compact && originNode && (typ.includes('round') || typ.includes('layering'))) {
      svgNodes.push({
        id: `${originNode.id}-return`,
        x: 88,
        y: 50,
        radius: 24,
        label: String(originNode.label || originNode.id),
        sublabel: 'Return',
        color: 'teal-dashed',
      });
    }
  }

  const nodeMap: Record<string, LayoutNode> = {};
  svgNodes.forEach((node) => {
    nodeMap[node.id] = node;
  });

  type EdgeDraft = LayoutArrow & { rawAmount: number; hubFlow?: boolean };
  const edgeDrafts: EdgeDraft[] = [];
  const hubId = hubNode ? String(hubNode.id) : null;
  const originId = originNode ? String(originNode.id) : null;

  apiEdges.forEach((edge, index) => {
    const fromNode = nodeMap[String(edge.source)];
    const toNode = nodeMap[String(edge.target)];
    if (!fromNode || !toNode) return;
    const rawAmount = Number(edge.amount) || 0;
    const source = String(edge.source);
    const target = String(edge.target);
    const hubFlow =
      !!hubId &&
      (source === hubId || target === hubId || source === originId || target === originId);
    edgeDrafts.push({
      id: `edge-${index}`,
      from: { x: fromNode.x, y: fromNode.y },
      to: { x: toNode.x, y: toNode.y },
      amount: formatAmount(rawAmount),
      rawAmount,
      showLabel: false,
      hubFlow,
    });
  });

  if (!compact && hubNode && originNode) {
    const typ = (typology || '').toLowerCase();
    const returnNode = nodeMap[`${originNode.id}-return`];
    const hub = nodeMap[String(hubNode.id)];
    if (returnNode && hub && (typ.includes('round') || typ.includes('layering'))) {
      const inward = apiEdges
        .filter((e) => e.target === hubNode.id)
        .reduce((s, e) => s + Number(e.amount || 0), 0);
      edgeDrafts.push({
        id: 'edge-return',
        from: { x: hub.x, y: hub.y },
        to: { x: returnNode.x, y: returnNode.y },
        amount: formatAmount(inward * 0.6 || 0),
        rawAmount: inward,
        color: 'red',
        curved: true,
        showLabel: true,
        labelIndex: 0,
      });
    }
  }

  const maxEdges = mini ? 8 : compact ? Math.min(edgeDrafts.length, 12) : edgeDrafts.length;
  const capped = [...edgeDrafts]
    .sort((a, b) => {
      if (mini && a.hubFlow !== b.hubFlow) return (b.hubFlow ? 1 : 0) - (a.hubFlow ? 1 : 0);
      return b.rawAmount - a.rawAmount;
    })
    .slice(0, maxEdges);

  if (mini) {
    capped.slice(0, 2).forEach((edge, i) => {
      edge.showLabel = true;
      edge.labelIndex = i;
    });
  } else if (!compact) {
    const labelCount = Math.min(5, capped.length);
    capped.slice(0, labelCount).forEach((edge, i) => {
      edge.showLabel = true;
      edge.labelIndex = i;
    });
  }

  const svgArrows: LayoutArrow[] = capped.map(({ rawAmount: _, ...arrow }) => arrow);

  return { nodes: svgNodes, arrows: svgArrows };
}
