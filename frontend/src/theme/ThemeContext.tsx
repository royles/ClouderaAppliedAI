import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  ColorTheme,
  ThemeMode,
  persistTheme,
  readStoredTheme,
} from "./index";

type ThemeContextValue = {
  mode: ThemeMode;
  color: ColorTheme;
  setMode: (mode: ThemeMode) => void;
  setColor: (color: ColorTheme) => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const stored = readStoredTheme();
  const [mode, setModeState] = useState<ThemeMode>(stored.mode);
  const [color, setColorState] = useState<ColorTheme>(stored.color);

  const setMode = useCallback(
    (next: ThemeMode) => {
      setModeState(next);
      persistTheme(next, color);
    },
    [color],
  );

  const setColor = useCallback(
    (next: ColorTheme) => {
      setColorState(next);
      persistTheme(mode, next);
    },
    [mode],
  );

  const value = useMemo(
    () => ({ mode, color, setMode, setColor }),
    [mode, color, setMode, setColor],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return ctx;
}
