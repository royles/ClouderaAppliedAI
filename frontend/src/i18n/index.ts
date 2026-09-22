import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "../locales/en.json";
import he from "../locales/he.json";

export const LOCALE_STORAGE_KEY = "customer360.locale";

function applyDocumentLanguage(lng: string) {
  const root = document.documentElement;
  root.lang = lng.startsWith("he") ? "he" : "en";
  root.dir = lng.startsWith("he") ? "rtl" : "ltr";
}

const saved =
  typeof localStorage !== "undefined"
    ? localStorage.getItem(LOCALE_STORAGE_KEY)
    : null;
const initial = saved === "he" || saved === "en" ? saved : "en";

void i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    he: { translation: he },
  },
  lng: initial,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

applyDocumentLanguage(i18n.language);

i18n.on("languageChanged", (lng) => {
  applyDocumentLanguage(lng);
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, lng.startsWith("he") ? "he" : "en");
  } catch {
    /* private mode */
  }
});

export default i18n;

export function appIntlLocale(): string {
  return i18n.language?.startsWith("he") ? "he-IL" : "en-IL";
}
