export type ThemeMode = "light" | "dark";
export type ColorTheme = "blue" | "purple" | "green" | "red" | "teal";

export const THEME_MODE_KEY = "customer360.theme.mode";
export const THEME_COLOR_KEY = "customer360.theme.color";

export const COLOR_THEMES: ColorTheme[] = ["blue", "purple", "green", "red", "teal"];

export function normalizeThemeMode(raw: string | null | undefined): ThemeMode {
  return raw === "dark" ? "dark" : "light";
}

export function normalizeColorTheme(raw: string | null | undefined): ColorTheme {
  const v = (raw ?? "").trim().toLowerCase();
  if (COLOR_THEMES.includes(v as ColorTheme)) return v as ColorTheme;
  return "blue";
}

export function readStoredTheme(): { mode: ThemeMode; color: ColorTheme } {
  try {
    return {
      mode: normalizeThemeMode(localStorage.getItem(THEME_MODE_KEY)),
      color: normalizeColorTheme(localStorage.getItem(THEME_COLOR_KEY)),
    };
  } catch {
    return { mode: "light", color: "blue" };
  }
}

export function applyTheme(mode: ThemeMode, color: ColorTheme) {
  const root = document.documentElement;
  root.setAttribute("data-theme-mode", mode);
  root.setAttribute("data-color-theme", color);
  root.style.colorScheme = mode === "dark" ? "dark" : "light";
}

export function persistTheme(mode: ThemeMode, color: ColorTheme) {
  applyTheme(mode, color);
  try {
    localStorage.setItem(THEME_MODE_KEY, mode);
    localStorage.setItem(THEME_COLOR_KEY, color);
  } catch {
    /* private mode */
  }
}

/** Call before React render (main.tsx). */
export function initTheme() {
  const { mode, color } = readStoredTheme();
  applyTheme(mode, color);
}
