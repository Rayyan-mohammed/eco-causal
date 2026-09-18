import { useMemo } from "react";
import ReactFlow, { Background, Handle, MarkerType, Position } from "reactflow";
import "reactflow/dist/style.css";
import { layoutChain } from "../graphLayout";

const STATUS_COLOR = { ok: "#2f9e5c", warn: "#c98a1f", bad: "#d1453b" };

function edgeStatus(r) {
  if (!r.exists) return "bad";
  if (r.condition_satisfied === false) return "warn";
  if (r.condition_satisfied === null && r.edge?.condition) return "warn";
  return "ok";
}

function CausalNode({ data }) {
  return (
    <div className="whitespace-nowrap rounded-xl border-2 border-forest-400/60 bg-forest-50 px-3 py-2 text-xs font-medium text-forest-900 shadow-sm dark:border-forest-600 dark:bg-forest-900/70 dark:text-forest-100">
      <Handle type="target" position={Position.Left} className="!h-1.5 !w-1.5 !bg-forest-400" />
      {data.label}
      <Handle type="source" position={Position.Right} className="!h-1.5 !w-1.5 !bg-forest-400" />
    </div>
  );
}

const nodeTypes = { causal: CausalNode };

export default function ReasoningGraph({ edgeResults }) {
  const { nodes, edges } = useMemo(() => {
    if (!edgeResults?.length) return { nodes: [], edges: [] };
    const { nodeIds, positions } = layoutChain(edgeResults);
    const nodes = nodeIds.map((id) => ({
      id,
      type: "causal",
      position: positions.get(id),
      data: { label: id.replaceAll("_", " ") },
      draggable: false,
    }));
    const edges = edgeResults.map((r, i) => {
      const status = edgeStatus(r);
      return {
        id: `e${i}`,
        source: r.source,
        target: r.target,
        animated: status === "warn",
        style: { stroke: STATUS_COLOR[status], strokeWidth: 2.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: STATUS_COLOR[status] },
      };
    });
    return { nodes, edges };
  }, [edgeResults]);

  if (!edgeResults?.length) return null;

  return (
    <div className="h-44 overflow-hidden rounded-xl border border-black/5 bg-white/70 dark:border-white/10 dark:bg-black/20">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.35 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        zoomOnScroll={false}
        panOnDrag={false}
        preventScrolling={false}
      >
        <Background gap={16} size={1} color="#00000012" />
      </ReactFlow>
    </div>
  );
}
