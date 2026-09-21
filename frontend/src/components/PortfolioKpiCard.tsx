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
      <div className="portfolio-kpi-head">
        <span className="label portfolio-kpi-label">{label}</span>
        <strong className="portfolio-kpi-value">{loading ? "…" : value}</strong>
      </div>
      {sub ? <span className="muted small kpi-sub">{sub}</span> : null}
      {progress && !loading ? (
        <div className="portfolio-kpi-progress-row">
          {targetLabel ? (
            <span className="muted small kpi-target-line">Objective: {targetLabel}</span>
          ) : (
            <span className="kpi-target-line kpi-target-spacer" aria-hidden />
          )}
          <KpiThermometer progress={progress} />
        </div>
      ) : null}
    </div>
  );
}
