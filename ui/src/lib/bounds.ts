import type { Cluster, Position } from "../types";

export function isWithinParentBounds(
  position: Position,
  parent: Cluster | undefined,
  nodeSize: number = 20
): boolean {
  if (!parent || !parent.width || !parent.height) return true;

  const halfNode = nodeSize / 2;

  return (
    position.x >= parent.x - parent.width / 2 + halfNode &&
    position.x <= parent.x + parent.width / 2 - halfNode &&
    position.y >= parent.y - parent.height / 2 + halfNode &&
    position.y <= parent.y + parent.height / 2 - halfNode
  );
}

export function constrainToParentBounds(
  position: Position,
  parent: Cluster | undefined,
  nodeSize: number = 20
): Position {
  if (!parent || !parent.width || !parent.height) return position;

  const halfNode = nodeSize / 2;
  const halfWidth = parent.width / 2;
  const halfHeight = parent.height / 2;

  return {
    x: Math.min(
      Math.max(position.x, parent.x - halfWidth + halfNode),
      parent.x + halfWidth - halfNode
    ),
    y: Math.min(
      Math.max(position.y, parent.y - halfHeight + halfNode),
      parent.y + halfHeight - halfNode
    ),
  };
}
