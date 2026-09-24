import { useTranslation } from "react-i18next";

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation();

  const current = i18n.language?.startsWith("he") ? "he" : "en";

  return (
    <div className="lang-switcher" role="group" aria-label={t("app.language")}>
      <button
        type="button"
        className={`lang-switcher-btn${current === "en" ? " is-active" : ""}`}
        onClick={() => void i18n.changeLanguage("en")}
        aria-pressed={current === "en"}
      >
        {t("app.languageEn")}
      </button>
      <button
        type="button"
        className={`lang-switcher-btn${current === "he" ? " is-active" : ""}`}
        onClick={() => void i18n.changeLanguage("he")}
        aria-pressed={current === "he"}
      >
        {t("app.languageHe")}
      </button>
    </div>
  );
}
