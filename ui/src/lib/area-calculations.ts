interface Point {
  x: number;
  y: number;
}

export function calculateBoundingBox(points: Point[]) {
  if (points.length === 0) return { minX: 0, minY: 0, maxX: 0, maxY: 0 };

  return points.reduce(
    (bounds, point) => ({
      minX: Math.min(bounds.minX, point.x),
      minY: Math.min(bounds.minY, point.y),
      maxX: Math.max(bounds.maxX, point.x),
      maxY: Math.max(bounds.maxY, point.y),
    }),
    {
      minX: points[0].x,
      minY: points[0].y,
      maxX: points[0].x,
      maxY: points[0].y,
    }
  );
}

export function calculateClusterSize(children: Point[], paddingFactor = 1.5) {
  if (children.length === 0) return { size: 140, width: 50, height: 50 };

  const bounds = calculateBoundingBox(children);
  const width = bounds.maxX - bounds.minX;
  const height = bounds.maxY - bounds.minY;

  // Calculate diagonal length for better coverage
  const diagonal = Math.sqrt(width * width + height * height);

  // Use diagonal as base size and apply padding factor
  const baseSize = diagonal * paddingFactor;

  // Add padding proportional to the cluster size
  const padding = baseSize * 0.2; // 20% of baseSize as padding

  return {
    size: baseSize * 100, // Scale for visualization
    width: (width + padding) * paddingFactor,
    height: (height + padding) * paddingFactor,
  };
}
