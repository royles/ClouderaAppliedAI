import { KpiTargetProgress } from "../api";
import KpiThermometer from "./KpiThermometer";

type Props = {
  label: string;
  value: string;
  sub?: string;
  progress?: KpiTargetProgress | null;
  targetLabel?: string | null;
  loading?: boolean;
  onClick?: () => void;
  actionHint?: string;
};

export default function PortfolioKpiCard({
  label,
  value,
  sub,
  progress,
  targetLabel,
  loading,
  onClick,
  actionHint,
}: Props) {
  const interactive = Boolean(onClick) && !loading;
  return (
    <div
      className={`portfolio-kpi${progress ? " portfolio-kpi-with-thermo" : ""}${interactive ? " portfolio-kpi-action" : ""}`}
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
      onClick={interactive ? onClick : undefined}
      onKeyDown={
        interactive
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onClick?.();
              }
            }
          : undefined
      }
    >
      <div className="portfolio-kpi-head">
        <span className="label portfolio-kpi-label">{label}</span>
        <strong className="portfolio-kpi-value">{loading ? "…" : value}</strong>
      </div>
      {actionHint && interactive ? (
        <span className="muted small kpi-action-hint">{actionHint}</span>
      ) : null}
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
