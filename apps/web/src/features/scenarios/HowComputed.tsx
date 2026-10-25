import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { formatDateTime } from "../../lib/format";
import { figureText, inputText } from "./figureText";
import type { Figure, WhatIfEnvelope } from "./result";

interface Props { figure: Figure; envelope: WhatIfEnvelope; label?: string; onClose: () => void }

export function HowComputed({ figure, envelope, label, onClose }: Props) {
  const { t, i18n } = useTranslation();
  const ref = useRef<HTMLDialogElement>(null);
  const { how } = figure;

  useEffect(() => {
    const d = ref.current;
    if (d && !d.open) d.showModal();
    d?.querySelector("button")?.focus(); // native does this too; jsdom does not
  }, []);

  return (
    <dialog
      ref={ref}
      aria-labelledby="how-title"
      className="scenario-panel how"
      onClose={onClose}
      onKeyDown={(e) => { if (e.key === "Escape") { e.preventDefault(); ref.current?.close(); } }}
    >
      <div className="panel-wrap">
        <header className="panel-head">
          <h2 id="how-title">{label ?? t("how.title")}</h2>
          <button type="button" className="btn-icon" aria-label={t("how.close")} onClick={() => ref.current?.close()}>✕</button>
        </header>
        <div className="panel-body">
          <p><strong>{figureText(figure, i18n.language)}</strong></p>
          <p>{t("how.formula")}: <code className="formula">{how.formula}</code></p>
          <dl className="rows">
            {Object.entries(how.inputs).map(([k, v]) => (
              <div key={k}><dt>{k}</dt><dd>{inputText(v)}</dd></div>
            ))}
          </dl>
          <dl className="rows muted fs-xs">
            <div><dt>{t("how.as_of")}</dt><dd>{formatDateTime(envelope.data_snapshot)}</dd></div>
            <div><dt>{t("how.rules_version")}</dt><dd>{how.rules_version}</dd></div>
            <div><dt>{t("how.price_basis")}</dt><dd>{envelope.price_basis}</dd></div>
            <div><dt>{t("how.cite")}</dt><dd>{how.cite}</dd></div>
          </dl>
          {envelope.approximate && <p className="note-warn-block">⚠ {t("approximate.source_adjusted")}</p>}
        </div>
        <footer className="panel-foot">
          <button type="button" className="btn" onClick={() => ref.current?.close()}>{t("how.close")}</button>
        </footer>
      </div>
    </dialog>
  );
}

export function InfoButton({ figure, envelope, name }: { figure: Figure; envelope: WhatIfEnvelope; name: string }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const btn = useRef<HTMLButtonElement>(null);
  const label = t(`figure.${name}`, { defaultValue: name });
  return (
    <>
      <button ref={btn} type="button" className="btn-icon sm" aria-label={t("how.aria", { label })} onClick={() => setOpen(true)}>(i)</button>
      {open && (
        <HowComputed
          figure={figure}
          envelope={envelope}
          label={label}
          onClose={() => { setOpen(false); btn.current?.focus(); }}
        />
      )}
    </>
  );
}
