import { useState } from "react";
import { Cluster } from "@/types/analytics";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "./ui/resizable";
import { ClusterTree } from "./cluster-tree";
import ClusterDetail from "./cluster-details";

const ClusterVisualisation = ({ clusters }: { clusters: Cluster[] }) => {
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(
    null
  );
  const selectedCluster = clusters.find((c) => c.id === selectedClusterId);

  const updateSelectedCluster = (cluster: Cluster) => {
    setSelectedClusterId(cluster.id);
  };

  return (
    <div className="w-full px-2">
      <div className="space-y-1 mb-20">
        <h2 className="text-lg mt-4 font-medium">Clusters</h2>
        <p className="text-sm text-muted-foreground">
          Visualise your clusters here
        </p>
      </div>

      <ResizablePanelGroup
        className="min-h-[400px] bg-muted/5 border rounded-md w-full max-w-none"
        direction="horizontal"
      >
        <ResizablePanel defaultSize={50}>
          <ClusterDetail cluster={selectedCluster || null} />
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={50}>
          <ClusterTree
            clusters={clusters}
            selectedClusterId={selectedClusterId}
            onSelectCluster={updateSelectedCluster}
          />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
};

export default ClusterVisualisation;
