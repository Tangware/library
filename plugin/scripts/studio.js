// The studio's address, this machine's login and this folder's project name in the studio, for bin/tangware, bin/show.sh and the SessionStart hook.
const { execSync } = require("node:child_process");
const { readFileSync } = require("node:fs");
const { homedir } = require("node:os");
const { basename, join } = require("node:path");

const studio = process.env.STUDIO_URL ?? "https://tangware.com/studio";
const tokenFile = join(homedir(), ".config/tangware/token");
const token = () => {
  try {
    return readFileSync(tokenFile, "utf8").trim();
  } catch {
    return "";
  }
};
const requireToken = () => {
  const found = token();
  if (found) return found;
  console.error("You are not logged in to Tanġware. Run tangware login.");
  process.exit(1);
};
const gitAsk = (args, fallback) => {
  try {
    return execSync(`git ${args}`, { stdio: ["ignore", "pipe", "ignore"] }).toString().trim();
  } catch {
    return fallback;
  }
};
// This folder's path in its repo, "" at the repo's root: the project is the design in it.
const path = () => gitAsk("rev-parse --show-prefix", "").replace(/\/$/, "");
// The project's name: the repo, then "/" and the path.
const repo = () =>
  process.env.STUDIO_REPO ?? [basename(gitAsk("rev-parse --show-toplevel", process.cwd())), path()].filter(Boolean).join("/");

module.exports = { studio, tokenFile, token, requireToken, repo, path };
