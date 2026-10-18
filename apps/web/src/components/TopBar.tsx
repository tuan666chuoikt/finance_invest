import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";
import { ROUTES } from "../app/routes";

const LANGS = ["vi", "en"] as const;

// Minimal bar; FE-shell-bar replaces it (freshness chip, mobile menu, Alt+L).
export function TopBar() {
  const { t, i18n } = useTranslation();
  return (
    <header data-testid="top-bar">
      <strong>Finvest</strong>
      <nav aria-label="main">
        {ROUTES.map((r) => (
          <NavLink key={r.path} to={r.path}>
            {t(r.nameKey)}
          </NavLink>
        ))}
      </nav>
      <div role="group" aria-label={t("lang.label")}>
        {LANGS.map((l) => {
          const active = i18n.resolvedLanguage === l;
          return (
            <button
              key={l}
              type="button"
              aria-pressed={active}
              onClick={() => void i18n.changeLanguage(l)}
              style={active ? { fontWeight: 700, textDecoration: "underline" } : undefined}
            >
              {t(`lang.${l}`)}
            </button>
          );
        })}
      </div>
    </header>
  );
}
