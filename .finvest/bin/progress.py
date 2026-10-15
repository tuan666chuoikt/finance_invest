#!/usr/bin/env python3
"""Sprint progress from the activity log, compared with the plan.
usage: progress.py [--all | --since 'YYYY-MM-DD[ HH:MM]'] [--mark]
  default : what happened since the last checkpoint (the last progress report to the sponsor)
  --mark  : move the checkpoint to the end of the log (do this after reporting)
Reads <sprint>/activity.log, stories.tsv (story, pts, title, tasks) and milestones.tsv (id, name, due, tasks),
plus dag.json for the task list. Output is short on purpose: the Scrum Master relays it, never the raw reports."""
import collections, json, os, sys

ROOT = os.environ.get('FI_ROOT', '/home/stein/Desktop/Learning/finance_invest')
H = os.path.join(ROOT, '.finvest')
SPRINT = open(os.path.join(H, 'current-sprint')).read().strip()
S = os.path.join(H, 'sprints', SPRINT)
LOG, CP = os.path.join(S, 'activity.log'), os.path.join(S, 'activity.checkpoint')
args = sys.argv[1:]


def tsv(name):
    p = os.path.join(S, name)
    if not os.path.exists(p):
        return []
    return [l.rstrip('\n').split('\t') for l in open(p) if l.strip() and not l.startswith('#')]


def tasks_of(row):
    return [t for t in row[3].split(',') if t and t != '-'] if len(row) > 3 else []


rows = []
for l in (open(LOG) if os.path.exists(LOG) else []):
    if not l.strip() or l.startswith('#'):
        continue
    f = [x.strip() for x in l.split('|')]
    if len(f) >= 5:
        rows.append(dict(ts=f[0], role=f[1], task=f[2], ev=f[3], res=f[4], rep=f[5] if len(f) > 5 else '-'))

cp = int(open(CP).read().strip() or 0) if os.path.exists(CP) else 0
if '--all' in args:
    new = rows
elif '--since' in args:
    since = args[args.index('--since') + 1]
    new = [r for r in rows if r['ts'] >= since]
else:
    new = rows[cp:]

dag = os.path.join(S, 'dag.json')
dag_ids = [t['id'] for t in json.load(open(dag))['tasks']] if os.path.exists(dag) else []
last = {}
for r in rows:
    last[r['task'].split()[-1]] = r  # "#12 FE-board" -> FE-board
merged = {t for t, r in last.items() if r['ev'] == 'merged'}
blocked = {t: r for t, r in last.items() if r['ev'] in ('blocked', 'consult', 'stopped', 'red')}

print(f'== {SPRINT}: {len(new)} new log lines' + (f' since {new[0]["ts"]}' if new else ''))
if dag_ids:
    done = [t for t in dag_ids if t in merged]
    print(f'tasks merged {len(done)}/{len(dag_ids)}')
for r in new[-25:]:
    print(f"{r['ts'][5:]} {r['role']:<7} {r['task']:<22} {r['ev']:<8} {r['res'][:90]}")
if blocked:
    print('-- needs attention:')
    for t, r in blocked.items():
        print(f"  {t}: {r['ev']} — {r['res'][:100]} ({r['rep']})")
stories = tsv('stories.tsv')
if stories:
    pts_done = pts_all = 0
    for s in stories:
        pts = float(s[1]) if len(s) > 1 and s[1] else 0
        pts_all += pts
        if all(t in merged for t in tasks_of(s)):
            pts_done += pts
    print(f'-- stories: {pts_done:g}/{pts_all:g} points have all tasks merged')
for m in tsv('milestones.tsv'):
    left = [t for t in tasks_of(m) if t not in merged]
    print(f"-- milestone {m[0]} {m[1] if len(m) > 1 else ''} due {m[2] if len(m) > 2 else '?'}: "
          + ('all merged' if not left else f'{len(left)} left: {", ".join(left[:8])}'))
if '--mark' in args:
    open(CP, 'w').write(str(len(rows)))
    print(f'checkpoint -> {len(rows)}')
