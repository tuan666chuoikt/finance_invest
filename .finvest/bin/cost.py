#!/usr/bin/env python3
"""Session cost in USD at API list prices (API-equivalent value; a subscription is not billed these dollars).

Usage: cost.py [SESSION_ID ...] [--all] [--since 'YYYY-MM-DD HH:MM'] [--by-part]
  no SESSION_ID -> the newest session of this project; --all -> every session.
  --by-part     -> split main session vs each subagent / workflow transcript.
Reads ~/.claude/projects/<project>/<session>.jsonl and every subagent/workflow transcript under <session>/,
counts each API message once (last line wins), prices it. A floor, not exact: transcripts under-record
output tokens. Update PRICE from the claude-api skill when prices change.
"""
import glob, json, os, sys
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.environ.get('FI_ROOT', '/home/stein/Desktop/Learning/finance_invest')
PROJ = os.path.expanduser('~/.claude/projects/' + ROOT.replace('/', '-').replace('_', '-'))
# $/MTok: input, output, cache read. Cache writes: 5 min = 1.25x input, 1 h = 2x input.
PRICE = {  # claude-api skill table, cached 2026-10-06
    'claude-fable-5-1': (10.0, 50.0, 0.25),
    'claude-opus-5-5': (4.0, 20.0, 0.20),
    'claude-sonnet-5-5': (2.0, 10.0, 0.20),
    'claude-haiku-5-5': (0.10, 0.50, 0.01),  # cache read not listed; assumed 0.1x input
}


def model_key(m):
    for k in PRICE:
        if m and m.startswith(k):
            return k
    return m or '?'


def main(argv):
    since, by_part, ids = None, False, []
    it = iter(argv)
    for a in it:
        if a == '--all':
            ids = [os.path.basename(p)[:-6] for p in glob.glob(f'{PROJ}/*.jsonl')]
        elif a == '--since':
            since = datetime.strptime(next(it), '%Y-%m-%d %H:%M').astimezone(timezone.utc)
        elif a == '--by-part':
            by_part = True
        else:
            ids.append(a)
    if not ids:
        files = glob.glob(f'{PROJ}/*.jsonl')
        if not files:
            sys.exit(f'no transcripts in {PROJ}')
        ids = [os.path.basename(max(files, key=os.path.getmtime))[:-6]]
    seen = {}
    for sid in ids:
        for f in [f'{PROJ}/{sid}.jsonl'] + glob.glob(f'{PROJ}/{sid}/**/*.jsonl', recursive=True):
            rel = os.path.relpath(f, f'{PROJ}/{sid}')
            part = 'main' if rel.startswith('..') else rel.split(os.sep)[0] + '/' + os.path.basename(f)[:24]
            with open(f, errors='replace') as fh:
                for line in fh:
                    if '"usage"' not in line:
                        continue
                    try:
                        d = json.loads(line)
                    except ValueError:
                        continue
                    m = d.get('message') or {}
                    u = m.get('usage')
                    if not isinstance(u, dict) or not m.get('id'):
                        continue
                    if since and d.get('timestamp'):
                        if datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00')) < since:
                            continue
                    seen[m['id']] = (model_key(m.get('model')), u, part)
    tot = defaultdict(lambda: [0, 0, 0, 0, 0.0])  # in, out, cache read, cache write, usd
    parts = defaultdict(float)
    for mk, u, part in seen.values():
        if mk not in PRICE:
            continue
        pi, po, pr = PRICE[mk]
        cc = u.get('cache_creation') or {}
        w1h = cc.get('ephemeral_1h_input_tokens', 0) or 0
        w5m = (u.get('cache_creation_input_tokens', 0) or 0) - w1h
        i, o, r = u.get('input_tokens', 0) or 0, u.get('output_tokens', 0) or 0, u.get('cache_read_input_tokens', 0) or 0
        usd = (i * pi + o * po + r * pr + w5m * pi * 1.25 + w1h * pi * 2) / 1e6
        t = tot[mk]
        t[0] += i; t[1] += o; t[2] += r; t[3] += w5m + w1h; t[4] += usd
        parts[part] += usd
    print(f"{'model':<20}{'input':>12}{'output':>12}{'cache rd':>14}{'cache wr':>12}{'USD':>10}")
    for mk, t in sorted(tot.items(), key=lambda x: -x[1][4]):
        print(f'{mk:<20}{t[0]:>12,}{t[1]:>12,}{t[2]:>14,}{t[3]:>12,}{t[4]:>10.2f}')
    print(f"{'total':<70}{sum(t[4] for t in tot.values()):>10.2f}")
    if by_part:
        print('-- by part (top 15)')
        for p, usd in sorted(parts.items(), key=lambda x: -x[1])[:15]:
            print(f'{p:<60}{usd:>10.2f}')


if __name__ == '__main__':
    main(sys.argv[1:])
