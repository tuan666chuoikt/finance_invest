export const meta = {
  name: 'finvest-sprint',
  description: 'Run a Finvest sprint as one dependency graph: each task builds when its dependencies merge, within seat caps; dev -> lead -> (fresh dev fix -> lead); tells the Scrum Master only about consults, 3rd review rounds, sponsor decisions, dead agents and milestones',
  whenToUse: 'Started by /fi-build. Reads SPRINT_DIR/dag.json (owned by the software architect).',
  phases: [{ title: 'Load' }, { title: 'Build' }, { title: 'Consult' }, { title: 'Review' }, { title: 'Wait' }, { title: 'Chores' }],
}

// args: { sprint: 'sprint-01',
//   seats: { fe: 2, be: 2, ai: 1 }     concurrent developers per side
//   leads: { fe: 1, be: 1 }            concurrent lead reviews per side (ai PRs go to the BE lead)
//   skip: ['TASK', ...]                tasks to leave out
//   only: ['TASK', ...]                run only these (plus nothing else); omit for all
//   stage: { 'FE-board': 'fix' }      SM override of an open task's first stage
//   portable: true }                   session not opened in FI_ROOT (fi-* agent types not registered):
//                                      run general-purpose agents told to follow .claude/agents/<type>.md
const A = args
const R = '/home/stein/Desktop/Learning/finance_invest'
const FD = `${R}/.finvest`
const SD = `${FD}/sprints/${A.sprint}`
const WT = '/home/stein/Desktop/Learning/finance_invest-worktrees'
const DEV = { fe: 'fi-fe-dev', be: 'fi-be-dev', ai: 'fi-ai-engineer' }
const OWNER = { sa: ['fi-software-architect', 'fable'], ai: ['fi-ai-architect', 'fable'], pm: ['fi-pm', 'opus'], po: ['fi-po', 'fable'] }
const OWNERS = { type: 'array', items: { type: 'string', enum: ['sa', 'ai', 'pm', 'po'] } }
// shortcut: portable mode loses omitClaudeMd/maxTurns/cacheTtl from the agent frontmatter; open the session in FI_ROOT to get them.
const run = (prompt, o) => A.portable && o.agentType
  ? agent(`You are ${o.agentType}. First read ${R}/.claude/agents/${o.agentType}.md (your role definition) and follow it.\n\n${prompt}`, { ...o, agentType: 'general-purpose' })
  : agent(prompt, o)
const BUILD = { type: 'object', required: ['result', 'note'], properties: {
  result: { type: 'string', enum: ['DONE', 'CONSULTING', 'BLOCKED'] }, head: { type: 'string' }, pr: { type: 'string' },
  owners: OWNERS, blockedBy: { type: 'string', description: 'task id of an unmerged branch that edits the same lines, if that is the block' },
  note: { type: 'string', description: 'at most 5 lines' } } }
const LEAD = { type: 'object', required: ['verdict', 'note'], properties: {
  verdict: { type: 'string', enum: ['MERGED', 'CHANGES_REQUIRED', 'ESCALATE', 'BLOCKED'] },
  mergeSha: { type: 'string' }, owners: OWNERS, note: { type: 'string', description: 'at most 5 lines' } } }
const ANSWER = { type: 'object', required: ['needsSponsor', 'note'], properties: {
  needsSponsor: { type: 'boolean' }, note: { type: 'string', description: 'at most 5 lines' } } }
const LOAD = { type: 'object', required: ['tasks'], properties: { tasks: { type: 'array', items: { type: 'object',
  required: ['id', 'side', 'after', 'state'], properties: {
    id: { type: 'string' }, side: { type: 'string', enum: ['fe', 'be', 'ai'] }, milestone: { type: 'string' },
    after: { type: 'array', items: { type: 'string' } }, base: { type: 'string' },
    leadModel: { type: 'string', enum: ['sonnet', 'opus'] }, effort: { type: 'string', enum: ['high', 'medium'] },
    priority: { type: 'number' }, manual: { type: 'boolean' },
    state: { type: 'string', enum: ['merged', 'open', 'todo'] }, stage: { type: 'string', enum: ['review', 'fix'] } } } } } }
const WAITED = { type: 'object', required: ['merged'], properties: { merged: { type: 'array', items: { type: 'string' } } } }

const COMMON = `FI_ROOT=${R}, FI_DIR=${FD}, SPRINT_DIR=${SD}, worktrees under ${WT}. Follow ${FD}/briefs/common.md. Your last step is one activity-log line via ${FD}/bin/log.sh. Your structured note is at most 5 lines; detail goes in your report file.`
const branch = t => `task/${A.sprint}/${t.id}`

const buildPrompt = t => `Build task ${t.id} (${A.sprint}). ${COMMON}
Follow ${FD}/briefs/dev.md. Your task card: \`${FD}/bin/task.sh ${t.id}\`. Worktree ${WT}/${t.id} on branch ${branch(t)} from origin/${t.base || A.sprint}.
Before coding, check no unmerged origin/task/${A.sprint}/* branch edits the same lines you must change; if one does, return BLOCKED with blockedBy. If a design document is ambiguous, wrong or silent, write SPRINT_DIR/3-consult.${t.id}.md and return CONSULTING with owners (sa, ai, pm).
When done: 3-build.${t.id}.md written, pushed (sm.sh push, sm.sh pr), return DONE with head (40-char sha).`
const resumePrompt = t => `${buildPrompt(t)}
Continuation: the branch and worktree may hold earlier work (read SPRINT_DIR/3-build.${t.id}.md if present). Owners may have answered in SPRINT_DIR/3-consult.${t.id}.answer.*.md; follow them.`
const fixPrompt = t => `Fix round for task ${t.id} on branch ${branch(t)} in ${WT}/${t.id}. ${COMMON}
Follow ${FD}/briefs/dev.md step 9 (lean fix round): fix every must-fix in SPRINT_DIR/3-pr.${t.id}.md and follow any 3-consult.${t.id}.answer.*.md written since. Return DONE with the new head.`
const leadPrompt = (t, role) => `You are the ${role} tech lead. Review task ${t.id} (${branch(t)} -> ${A.sprint}, worktree ${WT}/${t.id}; add it on the branch if missing). ${COMMON}
Follow ${FD}/briefs/lead.md. Append your round to SPRINT_DIR/3-pr.${t.id}.md before any merge.
APPROVE -> merge with sm.sh merge, remove the clean worktree, return MERGED with mergeSha. CHANGES_REQUIRED -> must-fix items in 3-pr. ESCALATE with owners when the plan, contract or UX spec must decide. BLOCKED for anything that needs the Scrum Master or the sponsor (red base, behaviour-changing conflict, refused action).`

function sem(n) { const q = []; return {
  async take() { if (n > 0) { n--; return } await new Promise(r => q.push(r)) },
  give() { const r = q.shift(); if (r) r(); else n++ } } }
function deferred() { let resolve; const p = new Promise(r => { resolve = r }); return { p, resolve, done: false } }
const seatCfg = Object.assign({ fe: 2, be: 2, ai: 1 }, A.seats || {})
const leadCfg = Object.assign({ fe: 1, be: 1 }, A.leads || {})
const seats = { fe: sem(seatCfg.fe), be: sem(seatCfg.be), ai: sem(seatCfg.ai) }
const leadSem = { fe: sem(leadCfg.fe), be: sem(leadCfg.be) }
const withSem = async (s, fn) => { await s.take(); try { return await fn() } finally { s.give() } }

const notify = text => {
  log(text)
  return agent(`Send exactly this text to the main session with the SendMessage tool (to: "main"), then return "sent". If SendMessage is unavailable, return "unavailable".\n\n[finvest-sprint] ${text}`,
    { label: 'notify', phase: 'Chores', model: 'haiku', effort: 'low' })
}
const chores = () => agent(`In ${R} run \`${FD}/bin/sm.sh finvest "docs(finvest): ${A.sprint} artifacts (sprint workflow)"\` and return its last line. Do nothing else.`,
  { label: 'commit-finvest', phase: 'Chores', model: 'haiku', effort: 'low' })

const leadSide = t => (t.side === 'fe' ? 'fe' : 'be')
const dev = (t, prompt, label) => withSem(seats[t.side], () =>
  run(prompt, { label: `${label}:${t.id}`, phase: 'Build', agentType: DEV[t.side], model: 'sonnet', effort: t.effort || 'medium', schema: BUILD }))
const lead = t => withSem(leadSem[leadSide(t)], () =>
  run(leadPrompt(t, leadSide(t).toUpperCase()), { label: `lead-${leadSide(t)}:${t.id}`, phase: 'Review',
    agentType: 'fi-tech-lead', model: t.leadModel || 'sonnet', effort: t.leadModel === 'opus' ? 'high' : (t.effort || 'medium'), schema: LEAD }))
const consult = async (t, owners, where) => {
  const list = owners && owners.length ? owners : ['sa']
  const answers = await parallel(list.map(o => () => run(
    `Mode: consult. ${COMMON}\nFollow ${FD}/briefs/owner.md "Consult mode". Answer the questions addressed to you about task ${t.id} in ${where}. Update your own documents first (plan, dag.json, contracts, architecture or UX spec, archiving per the rules), then write SPRINT_DIR/3-consult.${t.id}.answer.${o}.md. Set needsSponsor=true if only the sponsor can decide.`,
    { label: `consult-${o}:${t.id}`, phase: 'Consult', agentType: OWNER[o][0], model: OWNER[o][1], schema: ANSWER })))
  const ok = answers.filter(Boolean)
  return { died: ok.length < list.length, needsSponsor: ok.some(a => a.needsSponsor), note: ok.map(a => a.note).join(' | ') }
}

// ---- load the graph (an agent reads it: the workflow has no file access) ----
phase('Load')
const L = await agent(`Read ${SD}/dag.json. Run \`git -C ${R} fetch -q origin\`. For every task return id, side, milestone, after, base, leadModel, effort, priority, manual, and its state:
- "merged" if \`git -C ${R} merge-base --is-ancestor origin/${branch({ id: '<id>' })} origin/${A.sprint}\` succeeds or \`git -C ${R} log --format=%s origin/${A.sprint} | grep -q '(<id>)$'\`;
- else "open" if origin/${branch({ id: '<id>' })} exists; set stage "fix" if the last verdict in ${SD}/3-pr.<id>.md is CHANGES_REQUIRED, else "review";
- else "todo".
Return the data only; change nothing.`, { label: 'load-dag', phase: 'Load', model: 'haiku', effort: 'low', schema: LOAD })
if (!L) return { error: 'load failed' }
const skip = new Set(A.skip || [])
const only = A.only ? new Set(A.only) : null
const all = L.tasks
for (const t of all) if (A.stage && A.stage[t.id] && t.state === 'open') t.stage = A.stage[t.id]
const mergedSet = new Set(all.filter(t => t.state === 'merged').map(t => t.id))
const runnable = all.filter(t => t.state !== 'merged' && !t.manual && !skip.has(t.id) && (!only || only.has(t.id)))
  .sort((a, b) => (a.priority ?? 99) - (b.priority ?? 99))
const D = {}
for (const t of all) D[t.id] = deferred()
for (const id of mergedSet) { D[id].done = true; D[id].resolve('MERGED') }
// only watch non-run tasks that some runnable task waits for (watching the rest burns haiku calls for nothing)
const needed = new Set(runnable.flatMap(t => t.after || []))
const watched = all.filter(t => !mergedSet.has(t.id) && !runnable.includes(t) && needed.has(t.id)).map(t => t.id)
log(`graph: ${all.length} tasks, ${mergedSet.size} merged, ${runnable.length} to run, ${watched.length} watched (manual/skipped)`)

const results = []
let merges = 0
const announced = new Set()
const milestoneCheck = m => {
  if (!m || announced.has(m)) return
  const left = all.filter(x => x.milestone === m && !mergedSet.has(x.id))
  if (!left.length) { announced.add(m); notify(`Milestone ${m}: every task merged. Time for the full side runs and /fi-test.`) }
}
const settle = (t, r) => {
  results.push({ id: t.id, ...r })
  D[t.id].done = true; D[t.id].resolve(r.status)
  if (r.status === 'MERGED') {
    mergedSet.add(t.id); merges++
    log(`${t.id}: MERGED ${r.mergeSha ? r.mergeSha.slice(0, 8) : ''}`)
    if (merges % 4 === 0) chores()
    milestoneCheck(t.milestone)
  } else if (r.status !== 'SKIPPED') {
    notify(`${t.id}: ${r.status}. ${r.note || ''}`)
  }
}

// ---- watcher for manual/skipped tasks: a haiku helper checks about every 10 minutes ----
let stopWatch = false
const watcher = (async () => {
  let idle = 0
  for (let round = 0; round < 60 && !stopWatch; round++) {
    const pending = watched.filter(id => !D[id].done)
    if (!pending.length) break
    // a wait agent that returns at once (no 10-min Bash wait) would spin; stop after 3 such rounds and tell the SM
    if (idle >= 3) { notify(`watcher stopped: wait agents return without waiting; pending ${pending.join(', ')} — SM checks merges by hand`); break }
    const w = await agent(`Run this Bash command with the Bash tool timeout set to 600000 ms: \`${FD}/bin/wait-merged.sh ${A.sprint} - ${pending.join(' ')}\`. Return the task ids it printed as merged (empty list if none). Run nothing else, never a bare sleep.`,
      { label: `wait-${round}`, phase: 'Wait', model: 'haiku', effort: 'low', schema: WAITED })
    if (!w || !(w.merged || []).length) idle++; else idle = 0
    for (const id of (w && w.merged) || []) {
      if (!D[id] || D[id].done) continue
      D[id].done = true; D[id].resolve('MERGED'); mergedSet.add(id)
      log(`${id}: merged (watched)`)
      const t = all.find(x => x.id === id); if (t) milestoneCheck(t.milestone)
    }
  }
  for (const id of watched) if (!D[id].done) { D[id].done = true; D[id].resolve('NOT_MERGED') }
})()

// ---- one task: build -> review -> merge; stop on the 3rd consult or review round ----
async function runTask(t) {
  let consults = 0, rounds = 0
  const fix = async () => {
    let f = await dev(t, fixPrompt(t), 'fix')
    while (f && f.result === 'CONSULTING') {  // a fix round may consult too (e.g. size stop); route it like a build consult
      if (++consults > 2) return { status: 'STOP', note: 'third consult round: replan needed' }
      const c = await consult(t, f.owners, `SPRINT_DIR/3-consult.${t.id}.md`)
      if (c.died) return { status: 'AGENT_DIED', note: 'consult owner died' }
      if (c.needsSponsor) return { status: 'SPONSOR', note: c.note }
      f = await dev(t, fixPrompt(t), 'fix')
    }
    if (!f) return { status: 'AGENT_DIED', note: 'developer died' }
    if (f.result !== 'DONE') return { status: f.result, note: f.note }
    return null
  }
  if (t.state === 'todo') {
    let b = await dev(t, buildPrompt(t), 'build')
    for (;;) {
      if (b && b.result === 'BLOCKED' && b.blockedBy && D[b.blockedBy] && !D[b.blockedBy].done) {
        log(`${t.id}: waits for ${b.blockedBy} (same lines)`)
        const s = await D[b.blockedBy].p
        if (s !== 'MERGED') return { status: 'BLOCKED', note: `blocked by ${b.blockedBy}, which ended ${s}` }
        b = await dev(t, resumePrompt(t), 'resume')
        continue
      }
      if (b && b.result === 'CONSULTING') {
        if (++consults > 2) return { status: 'STOP', note: 'third consult round: replan needed' }
        notify(`${t.id}: consult round ${consults} to ${(b.owners || ['sa']).join('+')}`)
        const c = await consult(t, b.owners, `SPRINT_DIR/3-consult.${t.id}.md`)
        if (c.died) return { status: 'AGENT_DIED', note: 'consult owner died' }
        if (c.needsSponsor) return { status: 'SPONSOR', note: c.note }
        b = await dev(t, resumePrompt(t), 'resume')
        continue
      }
      break
    }
    if (!b) return { status: 'AGENT_DIED', note: 'developer died' }
    if (b.result !== 'DONE') return { status: b.result, note: b.note }
    log(`${t.id}: built ${b.head ? b.head.slice(0, 8) : ''}`)
  } else if (t.stage === 'fix') {
    rounds = 1
    const e = await fix(); if (e) return e
  }
  for (;;) {
    const v = await lead(t)
    if (!v) return { status: 'AGENT_DIED', note: 'lead died' }
    if (v.verdict === 'MERGED') return { status: 'MERGED', mergeSha: v.mergeSha, note: v.note }
    if (v.verdict === 'BLOCKED') return { status: 'BLOCKED', note: v.note }
    if (++rounds > 2) return { status: 'STOP', note: 'third review round: SM decides' }
    if (v.verdict === 'ESCALATE') {
      if (++consults > 2) return { status: 'STOP', note: 'third consult round: replan needed' }
      const c = await consult(t, v.owners, `the ESCALATE section of SPRINT_DIR/3-pr.${t.id}.md`)
      if (c.died) return { status: 'AGENT_DIED', note: 'consult owner died' }
      if (c.needsSponsor) return { status: 'SPONSOR', note: c.note }
    }
    const e = await fix(); if (e) return e
  }
}

// ---- run every task as soon as its dependencies are merged ----
phase('Build')
const running = runnable.map(t => (async () => {
  const deps = (t.after || []).filter(id => D[id])
  const unknown = (t.after || []).filter(id => !D[id])
  if (unknown.length) log(`${t.id}: unknown deps ignored: ${unknown.join(', ')}`)
  const st = await Promise.all(deps.map(id => D[id].p))
  const bad = deps.filter((id, i) => st[i] !== 'MERGED')
  if (bad.length) return settle(t, { status: 'SKIPPED', note: `dependency not merged: ${bad.join(', ')}` })
  try { settle(t, await runTask(t)) } catch (e) { settle(t, { status: 'ERROR', note: String(e).slice(0, 300) }) }
})())
await Promise.all(running)
stopWatch = true
for (const id of watched) if (!D[id].done) { D[id].done = true; D[id].resolve('NOT_MERGED') }
await watcher
await chores()
const by = s => results.filter(r => r.status === s).map(r => r.id)
return { merged: by('MERGED'), skipped: results.filter(r => r.status === 'SKIPPED').map(r => `${r.id} (${r.note})`),
  stopped: results.filter(r => !['MERGED', 'SKIPPED'].includes(r.status)).map(r => `${r.id} ${r.status}: ${r.note}`) }
