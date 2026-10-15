# UX — Market rules page (R1)

Stories: F-002 (PR-001, PR-137), source F-001. Learning: L1. Owner: `fi-pm`.

## Purpose
Show every rule the simulator uses, its value, since when it applies, and whether it is verified, so the
sponsor learns the rules and knows which numbers to trust.

## Layout
- Header: "Market rules / Luật thị trường" · rules version (e.g. `rules v3, 15/10/2026`) · counts
  "18 verified · 9 unverified".
- Filter chips: venue (HOSE, HNX, UPCoM, all) · group (Sessions, Prices & bands, Tick sizes, Lots, Costs &
  tax, Settlement) · "Unverified only".
- Table per group, columns: Rule · Venue · Value · Effective from · Status · Source.
  - Value formats: bands "±7 %", fees "0,15 %", ticks "100 ₫", sessions "09:00–09:15".
  - Status: "✓ Verified (date, source)" or "⚠ Unverified" — icon + text, amber row background; never colour alone.
  - Source: link to the `vn-market.md` section (e.g. VN§3).
- Worked example box under "Prices & bands": "Reference 93.500 → ceiling 100.000, floor 87.000 (±7 %,
  rounded inward to tick 100)" computed live from the module, so changing a value changes the example.
- Rule history: a row with older values expands to show previous values and their `effective_from`.

## States
| State | Shown |
|---|---|
| Loading | Table skeleton, header counts as "—" |
| Empty | "Rules module not generated. Run `<generate command>`." |
| Error | "Could not load rules" + retry; no stale numbers shown |
| Partial | A group with no rules shows "No rules defined for this venue" |
| Stale data | n/a (rules are static data); header shows rules version date |

## Keyboard
- Filters reachable by Tab; Enter toggles; table rows expand with Enter/Space; `/` focuses a rule search box.

## Mobile width
- Table becomes cards: Rule + Value on top, status chip, then venue/effective/source.

## Copy
- All labels via translation keys (F-031); rule names in both languages are not required here (glossary does that).
- No disclaimer banner (reference page, not analysis).
