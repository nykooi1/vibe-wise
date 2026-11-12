import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { loadSkills } from "@earendil-works/pi-coding-agent";

test("Pi discovers Learn-light from the package's configured skill paths", async () => {
  const manifest = JSON.parse(await readFile("package.json", "utf8"));
  const result = loadSkills({
    cwd: process.cwd(),
    agentDir: path.join(process.cwd(), ".unused-agent"),
    skillPaths: manifest.pi.skills.map((skill: string) => path.resolve(skill)),
    includeDefaults: false,
  });
  assert.ok(result.skills.some((skill) => skill.name === "learn-light"));
  assert.deepEqual(result.diagnostics, []);
});
