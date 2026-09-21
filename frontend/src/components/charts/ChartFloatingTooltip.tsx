import { ReactNode, RefObject } from "react";
import { ChartTooltipPosition, computeTooltipFlip } from "./chartPointer";

type Props = {
  canvasRef: RefObject<HTMLElement | null>;
  position: ChartTooltipPosition | null;
  children: ReactNode;
};

export default function ChartFloatingTooltip({
  canvasRef,
  position,
  children,
}: Props) {
  if (!position) return null;
  const { flipX, flipY } = computeTooltipFlip(canvasRef.current, position);
  return (
    <div
      className={`chart-tooltip-floating${flipX ? " flip-x" : ""}${flipY ? " flip-y" : ""}`}
      style={{ left: position.x, top: position.y }}
      role="tooltip"
    >
      {children}
    </div>
  );
}
