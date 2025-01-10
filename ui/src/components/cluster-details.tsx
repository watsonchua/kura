import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { FolderOpen, MessageCircle } from "lucide-react";
import { Cluster } from "@/types/analytics";

interface ClusterDetailProps {
  cluster: Cluster | null;
}

export default function ClusterDetail({ cluster }: ClusterDetailProps) {
  if (!cluster) {
    return (
      <div className="h-full flex items-center justify-center text-muted-foreground">
        <div className="text-center">
          <FolderOpen className="h-12 w-12 mx-auto mb-4 opacity-20" />
          <p className="text-lg">Select a cluster to view details</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-background">
      <div className="flex items-center gap-3 p-4 border-b bg-card">
        <MessageCircle className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold">Cluster Details</h2>
      </div>

      <ScrollArea className="flex-1 px-6 py-4">
        <Card className="border-0 shadow-none">
          <CardHeader className="px-0 space-y-6">
            <div className="space-y-3">
              <CardTitle className="text-2xl font-bold text-left">
                {cluster.name}
              </CardTitle>
              <div className="flex flex-wrap gap-2">
                <Badge
                  variant="secondary"
                  className="px-3 py-1 rounded-lg text-sm"
                >
                  {cluster.count.toLocaleString()} conversations
                </Badge>
                <Badge
                  variant="outline"
                  className="px-3 py-1 rounded-lg text-sm font-mono"
                >
                  ID: {cluster.id}
                </Badge>
              </div>
            </div>
            <Separator className="bg-border/60" />
          </CardHeader>

          <CardContent className="px-0 space-y-8">
            <div className="space-y-3 text-left">
              <h3 className="text-base font-semibold">Description</h3>
              <p className="text-muted-foreground leading-relaxed">
                {cluster.description}
              </p>
            </div>

            <div className="space-y-3">
              <h3 className="text-base font-semibold">Chat IDs</h3>
              <div className="text-sm text-muted-foreground bg-muted/40 rounded-lg p-4 font-mono break-all">
                {cluster.chat_ids.slice(0, 5).join(",\n")}
                {cluster.chat_ids.length > 5 && "..."}
              </div>
            </div>

            {cluster.parent_id && (
              <div className="space-y-3">
                <h3 className="text-base font-semibold">Parent Cluster</h3>
                <Badge
                  variant="outline"
                  className="px-3 py-1 rounded-lg text-sm font-mono"
                >
                  {cluster.parent_id}
                </Badge>
              </div>
            )}
          </CardContent>
        </Card>
      </ScrollArea>
    </div>
  );
}
