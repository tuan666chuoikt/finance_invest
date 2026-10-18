import { useEffect } from "react";

/** "Alt+L" style combo (Alt + a letter). Ignored while typing in a field. Matches on `code` (Mac Alt+L yields "¬"). */
export function useHotkey(combo: string, fn: () => void) {
  useEffect(() => {
    const letter = combo.split("+")[1].toUpperCase();
    const onKey = (e: KeyboardEvent) => {
      if (!e.altKey || (e.code !== `Key${letter}` && e.key.toUpperCase() !== letter)) return;
      const el = e.target as HTMLElement | null;
      if (el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable)) return;
      e.preventDefault();
      fn();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [combo, fn]);
}
