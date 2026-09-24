import { ReactNode } from "react";
import { createPortal } from "react-dom";
import { ChartTooltipPosition, computeTooltipFlip } from "./chartPointer";

type Props = {
  position: ChartTooltipPosition | null;
  children: ReactNode;
};

const OFFSET = 12;

export default function ChartFloatingTooltip({ position, children }: Props) {
  if (!position || typeof document === "undefined") return null;
  const { flipX, flipY } = computeTooltipFlip(position);
  let transform = `translate(${OFFSET}px, ${OFFSET}px)`;
  if (flipX && flipY) {
    transform = `translate(calc(-100% - ${OFFSET}px), calc(-100% - ${OFFSET}px))`;
  } else if (flipX) {
    transform = `translate(calc(-100% - ${OFFSET}px), ${OFFSET}px)`;
  } else if (flipY) {
    transform = `translate(${OFFSET}px, calc(-100% - ${OFFSET}px))`;
  }

  return createPortal(
    <div
      className="chart-tooltip-floating"
      style={{
        position: "fixed",
        left: position.clientX,
        top: position.clientY,
        transform,
      }}
      role="tooltip"
    >
      {children}
    </div>,
    document.body,
  );
}
