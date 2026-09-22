import { useTranslation } from "react-i18next";
import { COLOR_THEMES, ColorTheme, ThemeMode } from "../theme";
import { useTheme } from "../theme/ThemeContext";

const SWATCH: Record<ColorTheme, string> = {
  blue: "#0f6db8",
  purple: "#7c52a8",
  green: "#3d9a6a",
  red: "#c25565",
  teal: "#2a9aad",
};

export default function AdminAppearancePanel() {
  const { t } = useTranslation();
  const { mode, color, setMode, setColor } = useTheme();

  return (
    <div className="admin-appearance">
      <fieldset className="admin-appearance-fieldset">
        <legend>{t("admin.appearance.modeLegend")}</legend>
        <div
          className="admin-appearance-segmented"
          role="group"
          aria-label={t("admin.appearance.modeLegend")}
        >
          {(["light", "dark"] as ThemeMode[]).map((m) => (
            <button
              key={m}
              type="button"
              className={`admin-appearance-segment${mode === m ? " is-active" : ""}`}
              aria-pressed={mode === m}
              onClick={() => setMode(m)}
            >
              {t(`admin.appearance.mode.${m}`)}
            </button>
          ))}
        </div>
      </fieldset>

      <fieldset className="admin-appearance-fieldset">
        <legend>{t("admin.appearance.colorLegend")}</legend>
        <p className="muted small">{t("admin.appearance.colorLede")}</p>
        <div
          className="admin-appearance-swatches"
          role="radiogroup"
          aria-label={t("admin.appearance.colorLegend")}
        >
          {COLOR_THEMES.map((id) => (
            <label
              key={id}
              className={`admin-appearance-swatch${color === id ? " is-active" : ""}`}
            >
              <input
                type="radio"
                name="color-theme"
                value={id}
                checked={color === id}
                onChange={() => setColor(id)}
              />
              <span
                className="admin-appearance-swatch-dot"
                style={{ background: SWATCH[id] }}
                aria-hidden
              />
              <span className="admin-appearance-swatch-label">
                {t(`admin.appearance.colors.${id}`)}
              </span>
            </label>
          ))}
        </div>
      </fieldset>
    </div>
  );
}
