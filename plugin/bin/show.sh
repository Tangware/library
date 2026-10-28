#!/usr/bin/env node
const { readFileSync } = require("node:fs");
const { studio, requireToken, repo: repoName } = require("../scripts/studio.js");
const usage = `usage: show.sh go <page> [--select <id>] [--highlight <id or selector>] [--title <text>] [--caption <text>] [--commit <sha>]
       show.sh tour <steps.json, or - for stdin>
       show.sh step <next | back | number>
       show.sh state
       show.sh map [commit]`;
const fail = () => { console.error(usage); process.exit(2); };
const [kind, ...rest] = process.argv.slice(2);
let action = null;
if (kind === "go" && rest[0]) {
  action = { go: rest.shift() };
  for (let i = 0; i < rest.length; i += 2) {
    const key = rest[i]?.replace(/^--/, "");
    if (!["select", "highlight", "title", "caption", "commit"].includes(key) || rest[i + 1] === undefined) fail();
    action[key] = rest[i + 1];
  }
} else if (kind === "tour" && rest[0]) action = { tour: JSON.parse(readFileSync(rest[0] === "-" ? 0 : rest[0], "utf8")) };
else if (kind === "step" && rest[0]) action = { step: /^\d+$/.test(rest[0]) ? Number(rest[0]) : rest[0] };
else if (kind !== "state" && kind !== "map") fail();
const auth = { authorization: `Bearer ${requireToken()}` };
const repo = repoName();
const base = `${studio}/api/repos/${encodeURIComponent(repo)}`;
const json = (r) => {
  if (r.status === 401) { console.error("Your Tanġware login was refused. Run tangware login again."); process.exit(1); }
  return r.json();
};
const printMap = (m) => {
  console.log(`${m.repo} at ${m.commit.slice(0, 7)}${m.built ? "" : " (not built yet: no parts or checks)"}. show.sh go <page> [--select <id>]:`);
  for (const p of m.pages) {
    console.log(`${p.id}: ${p.question}`);
    for (const s of p.select) console.log(`  ${s.id}${s.label === s.id ? "" : `  ${s.label}`}`);
  }
};
if (kind === "map") {
  fetch(`${base}/map${rest[0] ? `/${encodeURIComponent(rest[0])}` : ""}`, { headers: auth })
    .then(json)
    .then(printMap)
    .catch(() => { console.log(`the studio is not running at ${studio}`); });
  return;
}
const request = action ? fetch(`${base}/drive`, { method: "POST", headers: { "content-type": "application/json", ...auth }, body: JSON.stringify(action) }) : fetch(`${base}/drive/state`, { headers: auth });
request
  .then(json)
  .then((r) => {
    if (!action) console.log(r.step ? `step ${r.step} of ${r.of}: ${r.title ?? r.caption ?? ""} (${r.page ?? ""})` : "no tour is showing");
    else console.log(r.pages ? `shown on ${r.pages} studio page${r.pages === 1 ? "" : "s"}` : `no studio page is open for ${repo} at ${studio}`);
  })
  .catch(() => { console.log(`the studio is not running at ${studio}`); });
