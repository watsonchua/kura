import { useState, useRef, useEffect } from "react";
import {
  ScatterChart,
  Scatter,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Cluster } from "@/types/analytics";
import { Button } from "./ui/button";
import { ChevronDown, ChevronUp } from "lucide-react";

type Props = {
  clusters: Cluster[];
  levelMap: Map<number, Cluster[]>;
};

const ClusterListItem = ({
  cluster,
  isHovered,
}: {
  cluster: Cluster;
  isHovered: boolean;
}) => {
  return (
    <div
      id={cluster.id}
      className={`p-3 border-b hover:bg-accent/50 cursor-pointer ${
        isHovered ? "bg-accent" : ""
      }`}
    >
      <div className="font-medium">{cluster.name}</div>
      <div className="text-sm text-muted-foreground mt-1">
        {cluster.count.toLocaleString()} conversations
      </div>
      <div className="text-xs font-mono text-muted-foreground mt-1">
        ID: {cluster.id}
      </div>
      <div className="text-xs mt-4 font-mono text-muted-foreground mt-1">
        {cluster.description}
      </div>
    </div>
  );
};

const PointVisualisation = ({ levelMap }: Props) => {
  const [currentLevel, setCurrentLevel] = useState(0);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const currentNodes = levelMap.get(currentLevel) || [];
  const maxLevel = levelMap.size - 1;
  const nodeCoordinates = currentNodes.map((item) => ({
    label: item.name,
    x: item.x_coord,
    y: item.y_coord,
    id: item.id,
  }));

  useEffect(() => {
    if (hoveredNodeId) {
      const element = document.querySelector(`div[id="${hoveredNodeId}"]`);
      const viewport = scrollAreaRef.current?.querySelector(
        "[data-radix-scroll-area-viewport]"
      );

      if (element && viewport) {
        const elementRect = element.getBoundingClientRect();
        const viewportRect = viewport.getBoundingClientRect();

        // Check if element is outside viewport
        if (
          elementRect.top < viewportRect.top ||
          elementRect.bottom > viewportRect.bottom
        ) {
          viewport.scrollTo({
            top:
              (element as HTMLElement).offsetTop -
              viewport.clientHeight / 2 +
              element.clientHeight / 2,
            behavior: "smooth",
          });
        }
      }
    }
  }, [hoveredNodeId]);

  return (
    <div className="flex h-full">
      <div className="w-3/5 flex flex-col">
        <ResponsiveContainer width="100%" height={600}>
          <ScatterChart
            margin={{
              top: 20,
              right: 20,
              bottom: 20,
              left: 20,
            }}
            width={500}
            height={600}
          >
            <XAxis type="number" dataKey="x" />
            <YAxis type="number" dataKey="y" />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              content={({ payload }) => {
                if (payload && payload[0]) {
                  return (
                    <div className="bg-white p-2 border rounded shadow">
                      {payload[0].payload.label}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Scatter
              name="Current nodes"
              data={nodeCoordinates}
              fill="#8884d8"
              cursor="pointer"
              label={({ label }) => label}
              onMouseEnter={(data) => {
                if (data && data.id) {
                  setHoveredNodeId(data.id);
                }
              }}
              onMouseLeave={() => setHoveredNodeId(null)}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <div className="w-2/5 border-l">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="font-semibold">
            All Clusters - Level {currentLevel} ({currentNodes.length})
          </h3>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentLevel(currentLevel - 1)}
              disabled={currentLevel === 0}
            >
              <ChevronUp className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentLevel(currentLevel + 1)}
              disabled={currentLevel === maxLevel}
            >
              <ChevronDown className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <ScrollArea ref={scrollAreaRef} className="h-[calc(100%-4rem)]">
          <div className="p-4">
            {currentNodes.map((cluster) => (
              <ClusterListItem
                key={cluster.id}
                cluster={cluster}
                isHovered={hoveredNodeId === cluster.id}
              />
            ))}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
};

export default PointVisualisation;
