// The studio's address, this machine's login and this folder's project name in the studio, for bin/tangware, bin/show.sh and the SessionStart hook.
const { execSync } = require("node:child_process");
const { readFileSync } = require("node:fs");
const { homedir } = require("node:os");
const { join } = require("node:path");

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
// This repo's GitHub owner and name, from its origin remote.
const remote = () => {
  const [, owner, repo] = /github\.com[:/]([^/]+)\/(.+?)(\.git)?$/.exec(gitAsk("remote get-url origin", "")) ?? [];
  return owner && { owner, repo };
};
// The project's name, as the studio has it: the owner, the repo, then "/" and the path.
const repo = () => {
  if (process.env.STUDIO_REPO) return process.env.STUDIO_REPO;
  const found = remote();
  return found ? [found.owner, found.repo, path()].filter(Boolean).join("/") : "";
};
// The project's address in the studio's API, where "~" stands for each "/" of its name.
const projectApi = () => `${studio}/api/repos/${repo().replaceAll("/", "~")}`;

module.exports = { studio, tokenFile, token, requireToken, repo, path, remote, projectApi };
