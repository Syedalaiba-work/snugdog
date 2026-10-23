#!/usr/bin/env node
// Locates Blender and runs a pipeline script headless.
//   node assets/3d/scripts/blender.mjs build_hotdog.py [-- extra args]
// Resolution order: BLENDER_PATH env -> PATH -> common install locations.
import { spawnSync } from "node:child_process";
import { existsSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

function fromPath() {
  const probe = spawnSync(process.platform === "win32" ? "where" : "which", ["blender"], { encoding: "utf8" });
  const hit = probe.status === 0 ? probe.stdout.split(/\r?\n/).find(Boolean) : null;
  return hit && existsSync(hit) ? hit : null;
}

function fromInstallDirs() {
  const candidates = [];
  if (process.platform === "win32") {
    for (const root of [process.env.ProgramFiles, process.env["ProgramFiles(x86)"]].filter(Boolean)) {
      const base = join(root, "Blender Foundation");
      if (!existsSync(base)) continue;
      // newest version first
      for (const dir of readdirSync(base).sort().reverse()) candidates.push(join(base, dir, "blender.exe"));
    }
  } else if (process.platform === "darwin") {
    candidates.push("/Applications/Blender.app/Contents/MacOS/Blender");
  } else {
    candidates.push("/usr/bin/blender", "/usr/local/bin/blender", "/snap/bin/blender");
  }
  return candidates.find(existsSync) ?? null;
}

const fromEnv = process.env.BLENDER_PATH && existsSync(process.env.BLENDER_PATH) ? process.env.BLENDER_PATH : null;
const blender = fromEnv || fromPath() || fromInstallDirs();
if (!blender) {
  console.error("Blender not found. Install it or set BLENDER_PATH to the blender executable.");
  process.exit(1);
}

const [script, ...rest] = process.argv.slice(2);
if (!script) {
  const version = spawnSync(blender, ["--version"], { encoding: "utf8" });
  console.log(blender);
  console.log(version.stdout.split(/\r?\n/)[0]);
  process.exit(0);
}

const scriptPath = resolve(here, script);
const extra = rest[0] === "--" ? rest.slice(1) : rest;
const run = spawnSync(
  blender,
  ["-b", "--factory-startup", "--python-exit-code", "1", "--python", scriptPath, "--", ...extra],
  { stdio: "inherit" },
);
process.exit(run.status ?? 1);
