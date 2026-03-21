import { describe, it, expect, beforeEach } from "vitest";
import * as os from "node:os";
import * as fs from "node:fs";
import * as path from "node:path";
import * as crypto from "node:crypto";
import {
  initProject,
  loadConfig,
  registerProject,
  resolveProject,
  listRegistered,
  IKE_DIR,
  DIRECTORIES,
} from "../config.js";

function makeTempDir(): string {
  const dir = path.join(os.tmpdir(), `ike-test-${crypto.randomUUID()}`);
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

describe("initProject", () => {
  it("creates .ike/ directory structure", () => {
    const dir = makeTempDir();
    initProject(dir);
    for (const subdir of Object.values(DIRECTORIES)) {
      expect(fs.existsSync(path.join(dir, IKE_DIR, subdir))).toBe(true);
    }
  });

  it("writes ike.json with stable GUID", () => {
    const dir = makeTempDir();
    const config = initProject(dir, "test-project");
    expect(config.project).toBe("test-project");
    expect(config.id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
    );
    expect(config.version).toBe("0.1.0");
    expect(config.ike_path).toBe(IKE_DIR);
  });

  it("uses directory name as default project name", () => {
    const dir = makeTempDir();
    const config = initProject(dir);
    expect(config.project).toBe(path.basename(dir));
  });

  it("is idempotent — does not overwrite existing config", () => {
    const dir = makeTempDir();
    const first = initProject(dir, "original");
    const second = initProject(dir, "changed");
    expect(second.id).toBe(first.id);
    expect(second.project).toBe("original");
  });
});

describe("loadConfig", () => {
  it("returns null for uninitialized directory", () => {
    const dir = makeTempDir();
    expect(loadConfig(dir)).toBeNull();
  });

  it("returns config after init", () => {
    const dir = makeTempDir();
    const config = initProject(dir, "my-project");
    const loaded = loadConfig(dir);
    expect(loaded).not.toBeNull();
    expect(loaded!.id).toBe(config.id);
    expect(loaded!.project).toBe("my-project");
  });
});

describe("registerProject / resolveProject", () => {
  it("registers a project and resolves its GUID back to a path", () => {
    const dir = makeTempDir();
    initProject(dir, "reg-test");
    const { id } = registerProject(dir);
    const resolved = resolveProject(id);
    expect(resolved).toBe(path.resolve(dir));
  });

  it("throws for uninitialized directory", () => {
    const dir = makeTempDir();
    expect(() => registerProject(dir)).toThrow("No ike.json");
  });

  it("throws for unknown GUID", () => {
    expect(() => resolveProject("not-a-real-guid")).toThrow("Unknown project_id");
  });

  it("throws for missing project_id", () => {
    expect(() => resolveProject(undefined)).toThrow("Missing required parameter");
    expect(() => resolveProject("")).toThrow("Missing required parameter");
  });

  it("listRegistered returns all registered projects", () => {
    const dir1 = makeTempDir();
    const dir2 = makeTempDir();
    initProject(dir1, "p1");
    initProject(dir2, "p2");
    const { id: id1 } = registerProject(dir1);
    const { id: id2 } = registerProject(dir2);
    const list = listRegistered();
    const ids = list.map((p) => p.id);
    expect(ids).toContain(id1);
    expect(ids).toContain(id2);
  });

  it("registering same path twice returns same GUID", () => {
    const dir = makeTempDir();
    initProject(dir);
    const { id: id1 } = registerProject(dir);
    const { id: id2 } = registerProject(dir);
    expect(id1).toBe(id2);
  });
});
