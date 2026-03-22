import * as fs from "node:fs";
import * as path from "node:path";
import matter from "gray-matter";
import { safePath } from "./security.js";
import { IKE_DIR, DIRECTORIES } from "./config.js";

// ── Types ─────────────────────────────────────────────────────────────────────

export type TaskStatus = "To Do" | "In Progress" | "Done" | "Draft";
export type Priority = "high" | "medium" | "low";

export interface TaskFrontmatter {
  id: string;
  title: string;
  status: TaskStatus;
  priority?: Priority;
  created: string;
  updated?: string;
  milestone?: string;
  assignees?: string[];
  tags?: string[];
  dependencies?: string[];
  "acceptance-criteria"?: string[];
  "definition-of-done"?: string[];
  visionlog_goal_id?: string;
  blocked_reason?: string;
}

export interface MilestoneFrontmatter {
  id: string;
  title: string;
  status: "open" | "closed";
  created: string;
  due?: string;
}

export interface DocumentFrontmatter {
  id: string;
  title: string;
  created: string;
  updated?: string;
  tags?: string[];
}

export interface ParsedFile<T> {
  frontmatter: T;
  content: string;
  filePath: string;
}

// ── Read / Write ──────────────────────────────────────────────────────────────

export function readMarkdown<T>(filePath: string): ParsedFile<T> {
  const raw = fs.readFileSync(filePath, "utf-8");
  const parsed = matter(raw);
  return { frontmatter: parsed.data as T, content: parsed.content.trim(), filePath };
}

export function writeMarkdown<T extends object>(filePath: string, frontmatter: T, content: string): void {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(filePath, matter.stringify(content, frontmatter));
}

// ── ID generation ─────────────────────────────────────────────────────────────

function nextId(prefix: string, existing: string[]): string {
  const max = existing.reduce((acc, id) => {
    const match = id.match(new RegExp(`^${prefix}-(\\d+)$`, "i"));
    if (!match) return acc;
    const n = parseInt(match[1], 10);
    return isNaN(n) ? acc : Math.max(acc, n);
  }, 0);
  return `${prefix}-${String(max + 1).padStart(4, "0")}`;
}

// ── Tasks ─────────────────────────────────────────────────────────────────────

function taskDir(projectRoot: string, completed = false): string {
  return safePath(projectRoot, IKE_DIR, completed ? DIRECTORIES.COMPLETED : DIRECTORIES.TASKS);
}

export function listTasks(projectRoot: string, includeCompleted = false): ParsedFile<TaskFrontmatter>[] {
  const results: ParsedFile<TaskFrontmatter>[] = [];

  const dirs = [taskDir(projectRoot)];
  if (includeCompleted) dirs.push(taskDir(projectRoot, true));

  for (const dir of dirs) {
    if (!fs.existsSync(dir)) continue;
    fs.readdirSync(dir)
      .filter((f) => f.endsWith(".md"))
      .sort()
      .forEach((f) => {
        try {
          results.push(readMarkdown<TaskFrontmatter>(path.join(dir, f)));
        } catch {}
      });
  }
  return results;
}

export function nextTaskId(projectRoot: string): string {
  const existing = listTasks(projectRoot, true).map((t) => t.frontmatter.id);
  // Also check archive
  const archiveDir = safePath(projectRoot, IKE_DIR, DIRECTORIES.ARCHIVE);
  if (fs.existsSync(archiveDir)) {
    fs.readdirSync(archiveDir)
      .filter((f) => f.endsWith(".md"))
      .forEach((f) => {
        try {
          const parsed = readMarkdown<TaskFrontmatter>(path.join(archiveDir, f));
          existing.push(parsed.frontmatter.id);
        } catch {}
      });
  }
  return nextId("TASK", existing);
}

export function taskPath(projectRoot: string, id: string, title: string, completed = false): string {
  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 50);
  return safePath(projectRoot, IKE_DIR, completed ? DIRECTORIES.COMPLETED : DIRECTORIES.TASKS, `${id} - ${slug}.md`);
}

export function findTaskFile(projectRoot: string, id: string): string | null {
  const dirs = [
    safePath(projectRoot, IKE_DIR, DIRECTORIES.TASKS),
    safePath(projectRoot, IKE_DIR, DIRECTORIES.COMPLETED),
    safePath(projectRoot, IKE_DIR, DIRECTORIES.ARCHIVE),
  ];
  for (const dir of dirs) {
    if (!fs.existsSync(dir)) continue;
    const match = fs.readdirSync(dir).find((f) => f.startsWith(id));
    if (match) return path.join(dir, match);
  }
  return null;
}

export function listAllTasks(projectRoot: string): ParsedFile<TaskFrontmatter>[] {
  const results = listTasks(projectRoot, true);
  const archiveDir = safePath(projectRoot, IKE_DIR, DIRECTORIES.ARCHIVE);
  if (fs.existsSync(archiveDir)) {
    fs.readdirSync(archiveDir)
      .filter((f) => f.endsWith(".md"))
      .sort()
      .forEach((f) => {
        try { results.push(readMarkdown<TaskFrontmatter>(path.join(archiveDir, f))); } catch {}
      });
  }
  return results;
}

// ── Milestones ────────────────────────────────────────────────────────────────

function milestoneDir(projectRoot: string): string {
  return safePath(projectRoot, IKE_DIR, DIRECTORIES.MILESTONES);
}

export function listMilestones(projectRoot: string): ParsedFile<MilestoneFrontmatter>[] {
  const dir = milestoneDir(projectRoot);
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .sort()
    .map((f) => readMarkdown<MilestoneFrontmatter>(path.join(dir, f)));
}

export function nextMilestoneId(projectRoot: string): string {
  const existing = listMilestones(projectRoot).map((m) => m.frontmatter.id);
  return nextId("MS", existing);
}

export function milestonePath(projectRoot: string, id: string, title: string): string {
  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 50);
  return safePath(projectRoot, IKE_DIR, DIRECTORIES.MILESTONES, `${id} - ${slug}.md`);
}

export function findMilestoneFile(projectRoot: string, id: string): string | null {
  const dir = milestoneDir(projectRoot);
  if (!fs.existsSync(dir)) return null;
  const match = fs.readdirSync(dir).find((f) => f.startsWith(id));
  return match ? path.join(dir, match) : null;
}

// ── Documents ─────────────────────────────────────────────────────────────────

function documentDir(projectRoot: string): string {
  return safePath(projectRoot, IKE_DIR, DIRECTORIES.DOCUMENTS);
}

export function listDocuments(projectRoot: string): ParsedFile<DocumentFrontmatter>[] {
  const dir = documentDir(projectRoot);
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .sort()
    .map((f) => readMarkdown<DocumentFrontmatter>(path.join(dir, f)));
}

export function nextDocumentId(projectRoot: string): string {
  const existing = listDocuments(projectRoot).map((d) => d.frontmatter.id);
  return nextId("DOC", existing);
}

export function documentPath(projectRoot: string, id: string, title: string): string {
  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 50);
  return safePath(projectRoot, IKE_DIR, DIRECTORIES.DOCUMENTS, `${id} - ${slug}.md`);
}

export function findDocumentFile(projectRoot: string, id: string): string | null {
  const dir = documentDir(projectRoot);
  if (!fs.existsSync(dir)) return null;
  const match = fs.readdirSync(dir).find((f) => f.startsWith(id));
  return match ? path.join(dir, match) : null;
}
