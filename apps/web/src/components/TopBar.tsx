import { useState } from "react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";
import { ROUTES } from "../app/routes";
import { useCrawlJob } from "../app/useCrawlJob";
import { CrawlButton } from "./CrawlButton";
import { CrawlStatus } from "./CrawlStatus";
import { FreshnessChip } from "./FreshnessChip";
import { LangSwitch } from "./LangSwitch";

// Below 768 px the nav hides behind the menu button; CSS only, so jsdom tests see both.
const CSS = `
.tb{display:flex;flex-wrap:wrap;align-items:center;gap:12px}
.tb-menu{display:none}
@media (max-width:767px){.tb-menu{display:inline-block}.tb-nav{display:none;width:100%}.tb-nav[data-open=true]{display:flex;flex-direction:column}}
.tb-nav{display:flex;gap:12px}`;

export function TopBar() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const crawl = useCrawlJob();
  return (
    <header data-testid="top-bar" className="tb">
      <style>{CSS}</style>
      <strong>Finvest</strong>
      <button type="button" className="tb-menu" aria-expanded={open} aria-controls="main-nav" onClick={() => setOpen(!open)}>
        {t("shell.menu")}
      </button>
      <nav id="main-nav" className="tb-nav" data-open={open} aria-label="main">
        {ROUTES.map((r) => (
          <NavLink key={r.path} to={r.path} onClick={() => setOpen(false)}>
            {t(r.nameKey)}
          </NavLink>
        ))}
      </nav>
      <FreshnessChip />
      <CrawlButton job={crawl.job} running={crawl.running} onClick={crawl.start} />
      <LangSwitch />
      <CrawlStatus job={crawl.job} refused={crawl.refused} />
    </header>
  );
}
