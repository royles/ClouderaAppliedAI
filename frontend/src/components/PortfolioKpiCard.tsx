import { KpiTargetProgress } from "../api";
import KpiThermometer from "./KpiThermometer";

type Props = {
  label: string;
  value: string;
  sub?: string;
  progress?: KpiTargetProgress | null;
  targetLabel?: string | null;
  loading?: boolean;
};

export default function PortfolioKpiCard({
  label,
  value,
  sub,
  progress,
  targetLabel,
  loading,
}: Props) {
  return (
    <div className={`portfolio-kpi${progress ? " portfolio-kpi-with-thermo" : ""}`}>
      <span className="label">{label}</span>
      <strong>{loading ? "…" : value}</strong>
      {sub ? <span className="muted small kpi-sub">{sub}</span> : null}
      {progress && targetLabel && !loading ? (
        <span className="muted small kpi-target-line">Objective: {targetLabel}</span>
      ) : null}
      {progress && !loading ? <KpiThermometer progress={progress} /> : null}
    </div>
  );
}
