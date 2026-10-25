import { useState } from "react";
import { useTranslation } from "react-i18next";
import { NavLink, useLocation } from "react-router-dom";
import { ROUTES } from "../app/routes";
import { useCrawlJob } from "../app/useCrawlJob";
import { CrawlButton } from "./CrawlButton";
import { Disclaimer } from "./Disclaimer";
import { CrawlStatus } from "./CrawlStatus";
import { FreshnessChip } from "./FreshnessChip";
import { LangSwitch } from "./LangSwitch";

export function TopBar() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const crawl = useCrawlJob();
  const analysis = ROUTES.find((r) => r.path === useLocation().pathname)?.analysis;
  return (
    <>
      <header data-testid="top-bar" className="tb">
        <div className="tb-inner">
          <strong className="tb-brand">Finvest</strong>
          <button type="button" className="tb-menu btn-icon" aria-label={t("shell.menu")} aria-expanded={open} aria-controls="main-nav" onClick={() => setOpen(!open)}>
            <span aria-hidden="true">☰</span>
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
        </div>
      </header>
      {analysis && <Disclaimer />}
      <CrawlStatus job={crawl.job} refused={crawl.refused} startError={crawl.startError} />
    </>
  );
}
