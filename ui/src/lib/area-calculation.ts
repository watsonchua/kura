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

export function calculateClusterSize(children: Point[], paddingFactor = 1.2) {
  if (children.length === 0) return { size: 100, width: 10, height: 10 };

  const bounds = calculateBoundingBox(children);
  const width = bounds.maxX - bounds.minX;
  const height = bounds.maxY - bounds.minY;

  // Base size on the larger dimension
  const baseSize = Math.max(width, height) * paddingFactor;

  return {
    size: baseSize * 100, // Scale for visualization
    width: width * paddingFactor,
    height: height * paddingFactor,
  };
}
