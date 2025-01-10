"use client";

import { useState, useMemo } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { calculateClusterSize } from "../lib/area-calculation";
import { Cluster } from "../types/analytics";

// Example data structure
const rawClusters: Cluster[] = [
  {
    id: "1",
    title: "Technology",
    description: "Tech related clusters",
    x: 300,
    y: 400,
    color: "#ffcdd2",
    children: [
      {
        id: "1-1",
        title: "Hardware",
        description: "Hardware components",
        x: 280,
        y: 380,
      },
      {
        id: "1-2",
        title: "Software",
        description: "Software systems",
        x: 320,
        y: 420,
      },
      {
        id: "1-3",
        title: "Networks",
        description: "Network systems",
        x: 290,
        y: 400,
      },
    ],
  },
  {
    id: "2",
    title: "Science",
    description: "Science related clusters",
    x: 600,
    y: 300,
    color: "#ffcc80",
    children: [
      {
        id: "2-1",
        title: "Physics",
        description: "Physics research",
        x: 580,
        y: 280,
      },
      {
        id: "2-2",
        title: "Chemistry",
        description: "Chemistry studies",
        x: 620,
        y: 320,
      },
      {
        id: "2-3",
        title: "Biology",
        description: "Biological sciences",
        x: 590,
        y: 310,
      },
    ],
  },
];

export default function BubbleVisualization() {
  const [activeParent, setActiveParent] = useState<string | null>(null);

  // Calculate parent cluster sizes based on their children
  const parentClusters = useMemo(() => {
    return rawClusters.map((cluster) => {
      if (!cluster.children?.length) return cluster;

      const { size, width, height } = calculateClusterSize(
        cluster.children,
        3 // 50% padding around children
      );

      return {
        ...cluster,
        size,
        width,
        height,
      };
    });
  }, []);

  // Flatten children for individual points
  const childClusters = parentClusters.flatMap(
    (parent) => parent.children || []
  );

  return (
    <div className="max-w-6xl mx-auto">
      <div className="w-full h-full min-h-[600px]  p-4">
        <ScatterChart
          width={1000}
          height={1000}
          margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" dataKey="x" name="X" unit="px" />
          <YAxis type="number" dataKey="y" name="Y" unit="px" />
          <ZAxis type="number" dataKey="size" range={[100, 2000]} />
          <Tooltip
            content={({ payload }) => {
              if (payload && payload[0]) {
                const data = payload[0].payload as Cluster;
                return (
                  <>
                    {data.children && (
                      <p className="text-sm text-gray-500 mt-2">
                        Contains {data.children.length} sub-clusters
                      </p>
                    )}
                  </>
                );
              }
              return null;
            }}
          />
          <Legend />

          {/* Parent Clusters as Bubbles */}
          <Scatter
            name="Parent Clusters"
            data={parentClusters}
            fill="#8884d8"
            fillOpacity={0.3}
            stroke="#8884d8"
            strokeWidth={1}
            onMouseEnter={(data) => setActiveParent(data.id)}
            onMouseLeave={() => setActiveParent(null)}
          >
            {parentClusters.map((cluster) => (
              <g key={cluster.id}>
                <circle
                  cx={cluster.x}
                  cy={cluster.y}
                  r={Math.sqrt((cluster.size || 100) / Math.PI)}
                  fill={cluster.color || "#8884d8"}
                  fillOpacity={0.3}
                  stroke="#8884d8"
                  strokeWidth={1}
                />
                <text
                  x={cluster.x}
                  y={cluster.y}
                  textAnchor="middle"
                  dy="-20"
                  fill="#333"
                  fontSize="14"
                >
                  {cluster.title}
                </text>
              </g>
            ))}
          </Scatter>

          {/* Child Clusters as Small Points */}
          <Scatter
            name="Child Clusters"
            data={childClusters}
            fill="#82ca9d"
            fillOpacity={0.6}
            shape="circle"
            legendType="circle"
          >
            {childClusters.map((entry, index) => (
              <circle
                key={`child-${index}`}
                cx={entry.x}
                cy={entry.y}
                r={4}
                fill={activeParent === entry.parentId ? "#82ca9d" : "#82ca9d40"}
                className="transition-all duration-200"
              />
            ))}
          </Scatter>
        </ScatterChart>
      </div>
    </div>
  );
}
