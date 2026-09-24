import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useLocation, useSearchParams } from "react-router-dom";
import { isCopilotFocusSearch, stripCopilotFocus } from "./copilotNavigation";
import { useAgentCopilot } from "./agentCopilotContext";

export type MobilePane = "copilot" | "content";

const PHONE_MAX_WIDTH_PX = 640;

type MobileUxContextValue = {
  isPhone: boolean;
  mobilePane: MobilePane;
  mobileFocus: boolean;
  enterMobileContent: () => void;
  returnToMobileCopilot: () => void;
};

const MobileUxContext = createContext<MobileUxContextValue | null>(null);

export function MobileUxProvider({ children }: { children: ReactNode }) {
  const { setOpen } = useAgentCopilot();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [isPhone, setIsPhone] = useState(() =>
    typeof window !== "undefined"
      ? window.matchMedia(`(max-width: ${PHONE_MAX_WIDTH_PX}px)`).matches
      : false,
  );
  const [mobilePane, setMobilePane] = useState<MobilePane>("copilot");
  const wasPhoneRef = useRef(isPhone);

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${PHONE_MAX_WIDTH_PX}px)`);
    const onChange = () => setIsPhone(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    if (isPhone && !wasPhoneRef.current) {
      setMobilePane("copilot");
      setOpen(true);
    }
    if (!isPhone && wasPhoneRef.current) {
      setMobilePane("copilot");
      setOpen(true);
    }
    wasPhoneRef.current = isPhone;
  }, [isPhone, setOpen]);

  useEffect(() => {
    if (!isPhone) return;
    if (isCopilotFocusSearch(searchParams)) {
      setMobilePane("content");
      setOpen(false);
    }
  }, [isPhone, searchParams, setOpen, location.pathname]);

  const enterMobileContent = useCallback(() => {
    if (!isPhone) return;
    setMobilePane("content");
    setOpen(false);
  }, [isPhone, setOpen]);

  const returnToMobileCopilot = useCallback(() => {
    if (!isPhone) return;
    setMobilePane("copilot");
    setOpen(true);
    if (isCopilotFocusSearch(searchParams)) {
      setSearchParams(stripCopilotFocus(searchParams), { replace: true });
    }
  }, [isPhone, searchParams, setOpen, setSearchParams]);

  const mobileFocus = isPhone && mobilePane === "content";

  const value = useMemo(
    (): MobileUxContextValue => ({
      isPhone,
      mobilePane,
      mobileFocus,
      enterMobileContent,
      returnToMobileCopilot,
    }),
    [isPhone, mobilePane, mobileFocus, enterMobileContent, returnToMobileCopilot],
  );

  return <MobileUxContext.Provider value={value}>{children}</MobileUxContext.Provider>;
}

export function useMobileUx() {
  const ctx = useContext(MobileUxContext);
  if (!ctx) {
    throw new Error("useMobileUx must be used within MobileUxProvider");
  }
  return ctx;
}

export function useMobileFocus(): boolean {
  return useMobileUx().mobileFocus;
}
