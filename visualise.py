from helpers.types import Cluster
from rich import print
from rich.tree import Tree as RichTree

if __name__ == "__main__":
    with open("clusters.json", "r") as f:
        clusters = [Cluster.model_validate_json(line) for line in f]

    # Create a rich tree for better visualization
    rich_tree = RichTree("Clusters")

    # First create a mapping of cluster IDs to their objects
    cluster_map = {cluster.id: cluster for cluster in clusters}

    # Find root clusters (those without parents)
    root_clusters = [c for c in clusters if not c.parent_id]

    # Keep track of processed clusters to avoid duplicates
    processed_clusters = set()

    def add_children(parent_tree, parent_cluster):
        # Find all children of this cluster
        children = [c for c in clusters if c.parent_id == parent_cluster.id]
        for child in children:
            # Skip if we've already processed this cluster
            if child.id in processed_clusters:
                continue
            processed_clusters.add(child.id)

            # Create a node with cluster info
            child_node = parent_tree.add(
                f"[bold]{child.name}[/bold]\n"
                f"Description: {child.description}\n"
                f"Contains {child.count} conversations"
            )
            # Recursively add children
            add_children(child_node, child)

    # Add all root clusters and their children
    for root in root_clusters:
        if root.id not in processed_clusters:
            processed_clusters.add(root.id)
            root_node = rich_tree.add(
                f"[bold blue]{root.name}[/bold blue]\n"
                f"Description: {root.description}\n"
                f"Contains {root.count} conversations"
            )
            add_children(root_node, root)

    print("Combined View")
    print(rich_tree)
