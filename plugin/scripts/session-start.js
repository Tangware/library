// SessionStart: when this machine is logged in and the studio serves this repo, tell Claude to use the studio skill.
const { studio, token, repo } = require("./studio.js");

const found = token();
if (!found) process.exit(0);
const name = repo();
fetch(`${studio}/api/repos`, { headers: { authorization: `Bearer ${found}` }, signal: AbortSignal.timeout(3000) })
  .then((r) => (r.ok ? r.json() : []))
  .then((repos) => {
    if (!repos.some((r) => r.name === name)) return;
    const additionalContext = `The Tanġware studio is open at ${studio}, showing this repo (${name}). Use the studio skill: whenever you talk about something the studio shows, show it there. In your first reply, offer in one line to give the first tour of the studio (the studio skill has it written out).`;
    console.log(JSON.stringify({ hookSpecificOutput: { hookEventName: "SessionStart", additionalContext } }));
  })
  .catch(() => {})
  .finally(() => process.exit(0));
