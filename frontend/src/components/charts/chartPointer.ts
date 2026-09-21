import type { MouseEvent as ReactMouseEvent } from "react";

export type ChartTooltipPosition = { x: number; y: number };

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

export function svgPointFromClient(svg: SVGSVGElement, clientX: number, clientY: number) {
  const pt = svg.createSVGPoint();
  pt.x = clientX;
  pt.y = clientY;
  const ctm = svg.getScreenCTM();
  if (!ctm) return null;
  return pt.matrixTransform(ctm.inverse());
}

export function computeTooltipFlip(
  container: HTMLElement | null,
  position: ChartTooltipPosition,
): { flipX: boolean; flipY: boolean } {
  if (!container) return { flipX: false, flipY: false };
  return {
    flipX: position.x > container.clientWidth * 0.62,
    flipY: position.y > container.clientHeight * 0.55,
  };
}

export function chartPointerFromSvgEvent(
  e: ReactMouseEvent<SVGSVGElement>,
  svg: SVGSVGElement,
  canvas: HTMLElement,
  pointCount: number,
  width: number,
  padX: number,
): { index: number; position: ChartTooltipPosition } | null {
  if (pointCount <= 0) return null;
  const loc = svgPointFromClient(svg, e.clientX, e.clientY);
  if (!loc) return null;
  const index = indexFromSvgX(loc.x, pointCount, width, padX);
  const rect = canvas.getBoundingClientRect();
  return {
    index,
    position: {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    },
  };
}
