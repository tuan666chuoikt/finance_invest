import { useRef, useState, type KeyboardEvent } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "../../api/client";
import { useDeleteScenario, type Scenario } from "./api";

/** ⋯ menu: Edit / Delete. Roving focus with arrows, Esc closes (ux "Keyboard"). */
export function CardMenu({ scenario, onEdit }: { scenario: Scenario; onEdit: () => void }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);
  const list = useRef<HTMLDivElement>(null);
  const del = useDeleteScenario();

  const items = () => Array.from(list.current?.querySelectorAll<HTMLElement>('[role="menuitem"]') ?? []);
  const close = () => { setOpen(false); trigger.current?.focus(); };
  const onKey = (e: KeyboardEvent) => {
    const els = items();
    const i = els.indexOf(document.activeElement as HTMLElement);
    if (e.key === "Escape") { e.preventDefault(); close(); }
    else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      els[(i + (e.key === "ArrowDown" ? 1 : els.length - 1)) % els.length]?.focus();
    }
  };
  const err = del.error instanceof ApiError ? del.error.code : del.error ? "INTERNAL" : null;

  return (
    <span style={{ position: "relative" }}>
      <button ref={trigger} type="button" aria-haspopup="menu" aria-expanded={open}
        aria-label={t("card.menu", { symbol: scenario.symbol })}
        onClick={() => { setOpen(!open); setTimeout(() => items()[0]?.focus()); }}>⋯</button>
      {open && (
        <div ref={list} role="menu" onKeyDown={onKey}
          style={{ position: "absolute", right: 0, zIndex: 5, background: "Canvas", border: "1px solid GrayText" }}>
          <button role="menuitem" type="button" onClick={() => { setOpen(false); onEdit(); }}>{t("card.edit")}</button>
          <button role="menuitem" type="button" onClick={() => { setOpen(false); setConfirm(true); }}>{t("card.delete")}</button>
        </div>
      )}
      {confirm && (
        <dialog open aria-label={t("card.delete_confirm", { name: scenario.name })}
          onKeyDown={(e) => { if (e.key === "Escape") setConfirm(false); }}>
          <p>{t("card.delete_confirm", { name: scenario.name })}</p>
          {err && <p role="alert">{t(`error.${err}`, { defaultValue: t("error.INTERNAL") })}</p>}
          <button type="button" autoFocus disabled={del.isPending} onClick={() => del.mutate(scenario.id, { onSuccess: () => setConfirm(false) })}>
            {t("card.delete")}
          </button>
          <button type="button" onClick={() => setConfirm(false)}>{t("card.cancel")}</button>
        </dialog>
      )}
    </span>
  );
}
