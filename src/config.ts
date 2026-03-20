import * as fs from "node:fs";
import * as path from "node:path";
import * as crypto from "node:crypto";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface IkeConfig {
  id: string;
  version: string;
  project: string;
  created: string;
  ike_path: string;
}

const CONFIG_FILENAME = "ike.json";
export const IKE_DIR = ".ike";

export const DIRECTORIES = {
  TASKS: "tasks",
  COMPLETED: "completed",
  ARCHIVE: "archive",
  MILESTONES: "milestones",
  DOCUMENTS: "documents",
} as const;

// ── In-memory GUID → path registry ───────────────────────────────────────────
// Each MCP server process maintains its own map. No disk state. No singletons.
// The AI registers a project via project_set, then uses the GUID on every call.

const guidToPath: Map<string, string> = new Map();

export function registerProject(projectPath: string): { id: string; project: string } {
  const absPath = path.resolve(projectPath);
  const config = loadConfig(absPath);
  if (!config) {
    throw new Error(
      `No ike.json at ${absPath}. Call project_init first to initialize ike.md in this directory.`
    );
  }
  guidToPath.set(config.id, absPath);
  return { id: config.id, project: config.project };
}

export function lookupGuid(guid: string): string | null {
  return guidToPath.get(guid) ?? null;
}

export function listRegistered(): Array<{ id: string; path: string }> {
  return Array.from(guidToPath.entries()).map(([id, p]) => ({ id, path: p }));
}

export function resolveProject(projectId: unknown): string {
  if (!projectId || typeof projectId !== "string") {
    throw new Error(
      "Missing required parameter: project_id. " +
      "Call project_set with the project path to register it and get its GUID. " +
      "Or call project_init to create a new ike.md project."
    );
  }
  const projectPath = lookupGuid(projectId);
  if (!projectPath) {
    throw new Error(
      `Unknown project_id '${projectId}'. This project hasn't been registered in this session. ` +
      "Call project_set with the project path to register it. " +
      "The project_id is the 'id' field in the project's ike.json."
    );
  }
  return projectPath;
}

// ── Config I/O ────────────────────────────────────────────────────────────────

export function loadConfig(dir: string): IkeConfig | null {
  const configPath = path.join(dir, IKE_DIR, CONFIG_FILENAME);
  if (!fs.existsSync(configPath)) return null;
  try {
    return JSON.parse(fs.readFileSync(configPath, "utf-8")) as IkeConfig;
  } catch {
    return null;
  }
}

export function saveConfig(dir: string, config: IkeConfig): void {
  const ikeDir = path.join(dir, IKE_DIR);
  if (!fs.existsSync(ikeDir)) fs.mkdirSync(ikeDir, { recursive: true });
  fs.writeFileSync(path.join(ikeDir, CONFIG_FILENAME), JSON.stringify(config, null, 2) + "\n");
}

// ── Init ──────────────────────────────────────────────────────────────────────

export function initProject(targetDir: string, projectName?: string): IkeConfig {
  const ikeDir = path.join(targetDir, IKE_DIR);

  for (const dir of Object.values(DIRECTORIES)) {
    const fullPath = path.join(ikeDir, dir);
    if (!fs.existsSync(fullPath)) fs.mkdirSync(fullPath, { recursive: true });
  }

  // Don't overwrite existing config
  const existing = loadConfig(targetDir);
  if (existing) return existing;

  const config: IkeConfig = {
    id: crypto.randomUUID(),
    version: "0.1.0",
    project: projectName ?? path.basename(targetDir),
    created: new Date().toISOString().split("T")[0],
    ike_path: IKE_DIR,
  };

  saveConfig(targetDir, config);
  return config;
}
