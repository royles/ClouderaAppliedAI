import type { MouseEvent as ReactMouseEvent } from "react";

/** Viewport coordinates for a fixed-position tooltip that follows the pointer. */
export type ChartTooltipPosition = { clientX: number; clientY: number };

export function xForIndex(
  index: number,
  pointCount: number,
  width: number,
  padX: number,
): number {
  if (pointCount <= 1) return padX;
  const stepX = (width - padX * 2) / (pointCount - 1);
  return padX + index * stepX;
}

export function indexFromSvgX(
  x: number,
  pointCount: number,
  width: number,
  padX: number,
): number {
  if (pointCount <= 1) return 0;
  const stepX = (width - padX * 2) / (pointCount - 1);
  const raw = (x - padX) / stepX;
  return Math.max(0, Math.min(pointCount - 1, Math.round(raw)));
}

/** Map x to bar index when each period occupies an equal slot across the plot width. */
export function indexFromBarChartX(
  x: number,
  pointCount: number,
  width: number,
  padX: number,
): number {
  if (pointCount <= 0) return 0;
  if (pointCount === 1) return 0;
  const plotWidth = width - padX * 2;
  const slot = plotWidth / pointCount;
  const raw = (x - padX) / slot;
  return Math.max(0, Math.min(pointCount - 1, Math.floor(raw)));
}

export function xForBarCenter(
  index: number,
  pointCount: number,
  width: number,
  padX: number,
): number {
  if (pointCount <= 0) return padX;
  const plotWidth = width - padX * 2;
  const slot = plotWidth / pointCount;
  return padX + slot * index + slot / 2;
}

export function svgPointFromClient(svg: SVGSVGElement, clientX: number, clientY: number) {
  const pt = svg.createSVGPoint();
  pt.x = clientX;
  pt.y = clientY;
  const ctm = svg.getScreenCTM();
  if (!ctm) return null;
  return pt.matrixTransform(ctm.inverse());
}

export function computeTooltipFlip(position: ChartTooltipPosition): {
  flipX: boolean;
  flipY: boolean;
} {
  return {
    flipX: position.clientX > window.innerWidth * 0.72,
    flipY: position.clientY > window.innerHeight * 0.75,
  };
}

export function chartPointerFromSvgEvent(
  e: ReactMouseEvent<SVGElement>,
  svg: SVGSVGElement,
  pointCount: number,
  width: number,
  padX: number,
): { index: number; position: ChartTooltipPosition; svgX: number } | null {
  if (pointCount <= 0) return null;
  const loc = svgPointFromClient(svg, e.clientX, e.clientY);
  if (!loc) return null;
  const index = indexFromSvgX(loc.x, pointCount, width, padX);
  const plotMax = width - padX;
  const svgX = Math.max(padX, Math.min(plotMax, loc.x));
  return {
    index,
    position: { clientX: e.clientX, clientY: e.clientY },
    svgX,
  };
}
