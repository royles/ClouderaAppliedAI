import { useTranslation } from "react-i18next";
import { KpiTargetProgress } from "../api";

type Props = {
  progress: KpiTargetProgress;
};

export default function KpiThermometer({ progress }: Props) {
  const { t } = useTranslation();
  const fill = Math.min(100, Math.max(0, progress.progress_pct));
  const pctOfTarget =
    progress.direction === "lower"
      ? progress.actual <= progress.target
        ? t("business.kpi.thermo.atOrBelow")
        : t("business.kpi.thermo.ofLimit", {
            pct: Math.round((progress.actual / progress.target) * 100),
          })
      : t("business.kpi.thermo.ofObjective", {
          pct: Math.round((progress.actual / progress.target) * 100),
        });

  return (
    <div
      className={`kpi-thermo kpi-thermo-${progress.status}`}
      role="progressbar"
      aria-valuenow={fill}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={t("business.kpi.thermo.a11y", { status: progress.status, detail: pctOfTarget })}
      title={pctOfTarget}
    >
      <div className="kpi-thermo-track">
        <div className="kpi-thermo-fill" style={{ width: `${fill}%` }} />
      </div>
    </div>
  );
}
