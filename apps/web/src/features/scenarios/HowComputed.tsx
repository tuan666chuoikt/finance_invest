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
      onClose={onClose}
      onKeyDown={(e) => { if (e.key === "Escape") { e.preventDefault(); ref.current?.close(); } }}
    >
      <h2 id="how-title">{label ?? t("how.title")}</h2>
      <p><strong>{figureText(figure, i18n.language)}</strong></p>
      <p>{t("how.formula")}: <code>{how.formula}</code></p>
      <table>
        <thead><tr><th>{t("how.input")}</th><th>{t("how.value")}</th></tr></thead>
        <tbody>
          {Object.entries(how.inputs).map(([k, v]) => (
            <tr key={k}><td>{k}</td><td>{inputText(v)}</td></tr>
          ))}
        </tbody>
      </table>
      <dl>
        <dt>{t("how.as_of")}</dt><dd>{formatDateTime(envelope.data_snapshot)}</dd>
        <dt>{t("how.rules_version")}</dt><dd>{how.rules_version}</dd>
        <dt>{t("how.price_basis")}</dt><dd>{envelope.price_basis}</dd>
        <dt>{t("how.cite")}</dt><dd>{how.cite}</dd>
      </dl>
      {envelope.approximate && <p>{t("approximate.source_adjusted")}</p>}
      <button type="button" onClick={() => ref.current?.close()}>{t("how.close")}</button>
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
      <button ref={btn} type="button" aria-label={t("how.aria", { label })} onClick={() => setOpen(true)}>(i)</button>
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
