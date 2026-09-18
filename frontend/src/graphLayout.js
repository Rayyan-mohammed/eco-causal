// Simple left-to-right layered layout for the small directed chains the
// checker produces (a handful of nodes, rarely more than one branch).
// Not meant to generalize to large graphs — dagre would be overkill here.
export function layoutChain(edgeResults) {
  const nodeIds = [];
  const seen = new Set();
  edgeResults.forEach((r) => {
    [r.source, r.target].forEach((id) => {
      if (!seen.has(id)) {
        seen.add(id);
        nodeIds.push(id);
      }
    });
  });

  const depth = new Map(nodeIds.map((id) => [id, 0]));
  // Relax longest-path depth a few passes; these chains are tiny so this
  // converges immediately, no need for a real topological sort.
  for (let pass = 0; pass < nodeIds.length + 1; pass++) {
    edgeResults.forEach((r) => {
      const candidate = (depth.get(r.source) || 0) + 1;
      if (candidate > (depth.get(r.target) || 0)) depth.set(r.target, candidate);
    });
  }

  const columns = new Map();
  nodeIds.forEach((id) => {
    const d = depth.get(id) || 0;
    if (!columns.has(d)) columns.set(d, []);
    columns.get(d).push(id);
  });

  const X_GAP = 200;
  const Y_GAP = 76;
  const positions = new Map();
  [...columns.entries()].forEach(([d, ids]) => {
    ids.forEach((id, i) => {
      positions.set(id, { x: d * X_GAP, y: i * Y_GAP - ((ids.length - 1) * Y_GAP) / 2 });
    });
  });

  return { nodeIds, positions };
}
