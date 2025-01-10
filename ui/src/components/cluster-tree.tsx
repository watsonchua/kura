"use client";

import { useState } from "react";
import { ChevronRight, ChevronDown, FolderTree } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Cluster } from "@/types/analytics";

interface ClusterTreeProps {
  clusters: Cluster[];
  selectedClusterId: string | null;
  onSelectCluster: (cluster: Cluster) => void;
}

interface ClusterTreeItemProps {
  cluster: Cluster;
  allClusters: Cluster[];
  level: number;
  selectedClusterId: string | null;
  onSelectCluster: (cluster: Cluster) => void;
}

function ClusterTreeItem({
  cluster,
  allClusters,
  level,
  selectedClusterId,
  onSelectCluster,
}: ClusterTreeItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const childClusters = allClusters.filter((c) => c.parent_id === cluster.id);
  const hasChildren = childClusters.length > 0;
  const percentage = ((cluster.count / 10000) * 100).toFixed(1);

  return (
    <div className="text-md text-left">
      <div
        className={`
          flex items-center gap-2 py-2 px-3 hover:bg-accent/50 rounded-md cursor-pointer
          transition-colors duration-200
          ${
            selectedClusterId === cluster.id
              ? "bg-accent text-accent-foreground"
              : ""
          }
        `}
        style={{ paddingLeft: `${level * 16 + 12}px` }}
        onClick={() => onSelectCluster(cluster)}
      >
        {hasChildren ? (
          <Button
            variant="ghost"
            size="sm"
            className="h-4 w-4 p-0 hover:bg-transparent"
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
          >
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </Button>
        ) : (
          <div className="w-4" />
        )}
        <span className="flex-1 font-medium truncate">{cluster.name}</span>
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {percentage}% • {cluster.count.toLocaleString()} records
          {hasChildren && ` • ${childClusters.length} children`}
        </span>
      </div>
      {isExpanded &&
        childClusters.map((child) => (
          <ClusterTreeItem
            key={child.id}
            cluster={child}
            allClusters={allClusters}
            level={level + 1}
            selectedClusterId={selectedClusterId}
            onSelectCluster={onSelectCluster}
          />
        ))}
    </div>
  );
}

export function ClusterTree({
  clusters,
  selectedClusterId,
  onSelectCluster,
}: ClusterTreeProps) {
  const rootClusters = clusters.filter((cluster) => cluster.parent_id === null);

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-2 p-4 border-b">
        <FolderTree className="h-5 w-5 text-primary" />
        <h2 className="font-semibold">Cluster Hierarchy</h2>
      </div>
      <ScrollArea className="flex-1 p-2">
        <div className="space-y-0.5">
          {rootClusters.map((cluster) => (
            <ClusterTreeItem
              key={cluster.id}
              cluster={cluster}
              allClusters={clusters}
              level={0}
              selectedClusterId={selectedClusterId}
              onSelectCluster={onSelectCluster}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
