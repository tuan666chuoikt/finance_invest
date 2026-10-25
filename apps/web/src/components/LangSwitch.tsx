import { useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useHotkey } from "../lib/useHotkey";

const LANGS = ["vi", "en"] as const;

export function LangSwitch() {
  const { t, i18n } = useTranslation();
  const toggle = useCallback(() => void i18n.changeLanguage(i18n.resolvedLanguage === "en" ? "vi" : "en"), [i18n]);
  useHotkey("Alt+L", toggle);
  return (
    <div role="group" className="seg" aria-label={t("lang.label")}>
      {LANGS.map((l) => {
        const active = i18n.resolvedLanguage === l;
        return (
          <button
            key={l}
            type="button"
            aria-pressed={active}
            onClick={() => void i18n.changeLanguage(l)}
          >
            {t(`lang.${l}`)}
          </button>
        );
      })}
    </div>
  );
}
