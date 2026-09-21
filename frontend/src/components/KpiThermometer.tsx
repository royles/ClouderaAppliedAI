import { KpiTargetProgress } from "../api";

type Props = {
  progress: KpiTargetProgress;
};

export default function KpiThermometer({ progress }: Props) {
  const fill = Math.min(100, Math.max(0, progress.progress_pct));
  const pctOfTarget =
    progress.direction === "lower"
      ? progress.actual <= progress.target
        ? "At or below objective"
        : `${Math.round((progress.actual / progress.target) * 100)}% of limit`
      : `${Math.round((progress.actual / progress.target) * 100)}% of objective`;

  return (
    <div
      className={`kpi-thermo kpi-thermo-${progress.status}`}
      role="img"
      aria-label={`${progress.status} — ${pctOfTarget}`}
      title={pctOfTarget}
    >
      <div className="kpi-thermo-track">
        <div className="kpi-thermo-fill" style={{ height: `${fill}%` }} />
      </div>
      <div className="kpi-thermo-bulb" />
    </div>
  );
}
