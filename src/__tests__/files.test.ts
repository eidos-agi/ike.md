import { describe, it, expect, beforeEach } from "vitest";
import * as os from "node:os";
import * as fs from "node:fs";
import * as path from "node:path";
import * as crypto from "node:crypto";
import { initProject, IKE_DIR, DIRECTORIES } from "../config.js";
import {
  readMarkdown,
  writeMarkdown,
  listTasks,
  nextTaskId,
  taskPath,
  findTaskFile,
  listAllTasks,
  listMilestones,
  nextMilestoneId,
  milestonePath,
  findMilestoneFile,
  listDocuments,
  nextDocumentId,
  documentPath,
  findDocumentFile,
  type TaskFrontmatter,
  type MilestoneFrontmatter,
  type DocumentFrontmatter,
} from "../files.js";

function makeTempProject(name = "test"): string {
  const dir = path.join(os.tmpdir(), `ike-test-${crypto.randomUUID()}`);
  fs.mkdirSync(dir, { recursive: true });
  initProject(dir, name);
  return dir;
}

function createTask(projectRoot: string, id: string, title: string, status: TaskFrontmatter["status"] = "To Do"): string {
  const fm: TaskFrontmatter = {
    id,
    title,
    status,
    created: "2026-03-21",
  };
  const filePath = taskPath(projectRoot, id, title);
  writeMarkdown(filePath, fm, "");
  return filePath;
}

// ── readMarkdown / writeMarkdown ──────────────────────────────────────────────

describe("readMarkdown / writeMarkdown", () => {
  it("round-trips frontmatter and content", () => {
    const dir = makeTempProject();
    const filePath = path.join(dir, "test.md");
    const fm = { id: "TASK-0001", title: "Hello", status: "To Do" as const, created: "2026-03-21" };
    writeMarkdown(filePath, fm, "Some notes here.");
    const result = readMarkdown<TaskFrontmatter>(filePath);
    expect(result.frontmatter.id).toBe("TASK-0001");
    expect(result.frontmatter.title).toBe("Hello");
    expect(result.content).toBe("Some notes here.");
    expect(result.filePath).toBe(filePath);
  });

  it("creates parent directories if they don't exist", () => {
    const dir = makeTempProject();
    const filePath = path.join(dir, "deep", "nested", "file.md");
    writeMarkdown(filePath, { id: "DOC-0001", title: "t", created: "2026-03-21" }, "");
    expect(fs.existsSync(filePath)).toBe(true);
  });

  it("handles empty content", () => {
    const dir = makeTempProject();
    const filePath = path.join(dir, "empty.md");
    writeMarkdown(filePath, { id: "X" }, "");
    const result = readMarkdown<{ id: string }>(filePath);
    expect(result.content).toBe("");
  });
});

// ── Task ID sequencing ────────────────────────────────────────────────────────

describe("nextTaskId", () => {
  it("returns TASK-0001 for empty project", () => {
    const dir = makeTempProject();
    expect(nextTaskId(dir)).toBe("TASK-0001");
  });

  it("increments from existing tasks", () => {
    const dir = makeTempProject();
    createTask(dir, "TASK-0001", "First");
    expect(nextTaskId(dir)).toBe("TASK-0002");
  });

  it("uses max ID, not count (handles gaps)", () => {
    const dir = makeTempProject();
    createTask(dir, "TASK-0001", "First");
    createTask(dir, "TASK-0005", "Fifth");
    expect(nextTaskId(dir)).toBe("TASK-0006");
  });

  it("counts completed tasks in numbering sequence", () => {
    const dir = makeTempProject();
    // Write a task directly into the completed dir
    const fm: TaskFrontmatter = { id: "TASK-0003", title: "Done task", status: "Done", created: "2026-03-21" };
    const completedPath = path.join(dir, IKE_DIR, DIRECTORIES.COMPLETED, "TASK-0003 - done-task.md");
    writeMarkdown(completedPath, fm, "");
    expect(nextTaskId(dir)).toBe("TASK-0004");
  });

  it("counts archived tasks in numbering sequence", () => {
    const dir = makeTempProject();
    const fm: TaskFrontmatter = { id: "TASK-0007", title: "Archived", status: "To Do", created: "2026-03-21" };
    const archivePath = path.join(dir, IKE_DIR, DIRECTORIES.ARCHIVE, "TASK-0007 - archived.md");
    writeMarkdown(archivePath, fm, "");
    expect(nextTaskId(dir)).toBe("TASK-0008");
  });
});

// ── taskPath / slug ───────────────────────────────────────────────────────────

describe("taskPath", () => {
  it("places tasks in the tasks dir by default", () => {
    const dir = makeTempProject();
    const p = taskPath(dir, "TASK-0001", "My Task");
    expect(p).toContain(path.join(IKE_DIR, DIRECTORIES.TASKS));
  });

  it("places completed tasks in completed dir", () => {
    const dir = makeTempProject();
    const p = taskPath(dir, "TASK-0001", "My Task", true);
    expect(p).toContain(path.join(IKE_DIR, DIRECTORIES.COMPLETED));
  });

  it("slugifies the title", () => {
    const dir = makeTempProject();
    const p = taskPath(dir, "TASK-0001", "Hello World! Special Chars");
    expect(path.basename(p)).toBe("TASK-0001 - hello-world-special-chars.md");
  });

  it("truncates long titles to 50 chars in slug", () => {
    const dir = makeTempProject();
    const longTitle = "A".repeat(200);
    const p = taskPath(dir, "TASK-0001", longTitle);
    const slug = path.basename(p).replace("TASK-0001 - ", "").replace(".md", "");
    expect(slug.length).toBeLessThanOrEqual(50);
  });
});

// ── findTaskFile ──────────────────────────────────────────────────────────────

describe("findTaskFile", () => {
  it("finds a task in the tasks dir", () => {
    const dir = makeTempProject();
    const filePath = createTask(dir, "TASK-0001", "Active Task");
    expect(findTaskFile(dir, "TASK-0001")).toBe(filePath);
  });

  it("finds a task in the completed dir", () => {
    const dir = makeTempProject();
    const fm: TaskFrontmatter = { id: "TASK-0001", title: "Done", status: "Done", created: "2026-03-21" };
    const completedPath = taskPath(dir, "TASK-0001", "Done", true);
    writeMarkdown(completedPath, fm, "");
    expect(findTaskFile(dir, "TASK-0001")).toBe(completedPath);
  });

  it("finds a task in the archive dir", () => {
    const dir = makeTempProject();
    const fm: TaskFrontmatter = { id: "TASK-0001", title: "Archived", status: "To Do", created: "2026-03-21" };
    const archivePath = path.join(dir, IKE_DIR, DIRECTORIES.ARCHIVE, "TASK-0001 - archived.md");
    writeMarkdown(archivePath, fm, "");
    expect(findTaskFile(dir, "TASK-0001")).toBe(archivePath);
  });

  it("returns null for nonexistent task", () => {
    const dir = makeTempProject();
    expect(findTaskFile(dir, "TASK-9999")).toBeNull();
  });
});

// ── listTasks ─────────────────────────────────────────────────────────────────

describe("listTasks", () => {
  it("returns empty array for new project", () => {
    const dir = makeTempProject();
    expect(listTasks(dir)).toHaveLength(0);
  });

  it("lists active tasks sorted by filename", () => {
    const dir = makeTempProject();
    createTask(dir, "TASK-0002", "Second");
    createTask(dir, "TASK-0001", "First");
    const tasks = listTasks(dir);
    expect(tasks).toHaveLength(2);
    expect(tasks[0].frontmatter.id).toBe("TASK-0001");
    expect(tasks[1].frontmatter.id).toBe("TASK-0002");
  });

  it("does not include completed tasks by default", () => {
    const dir = makeTempProject();
    createTask(dir, "TASK-0001", "Active");
    const fm: TaskFrontmatter = { id: "TASK-0002", title: "Done", status: "Done", created: "2026-03-21" };
    writeMarkdown(taskPath(dir, "TASK-0002", "Done", true), fm, "");
    expect(listTasks(dir)).toHaveLength(1);
  });

  it("includes completed tasks when flag is set", () => {
    const dir = makeTempProject();
    createTask(dir, "TASK-0001", "Active");
    const fm: TaskFrontmatter = { id: "TASK-0002", title: "Done", status: "Done", created: "2026-03-21" };
    writeMarkdown(taskPath(dir, "TASK-0002", "Done", true), fm, "");
    expect(listTasks(dir, true)).toHaveLength(2);
  });
});

// ── Task lifecycle: complete ──────────────────────────────────────────────────

describe("task_complete lifecycle (filesystem)", () => {
  it("file moves from tasks/ to completed/ and is gone from tasks/", () => {
    const dir = makeTempProject();
    const srcPath = createTask(dir, "TASK-0001", "My Task");
    const task = readMarkdown<TaskFrontmatter>(srcPath);
    const destPath = taskPath(dir, "TASK-0001", "My Task", true);

    // Simulate what the server does
    const fm = { ...task.frontmatter, status: "Done" as const };
    writeMarkdown(destPath, fm, task.content);
    fs.unlinkSync(srcPath);

    expect(fs.existsSync(srcPath)).toBe(false);
    expect(fs.existsSync(destPath)).toBe(true);
    const completed = readMarkdown<TaskFrontmatter>(destPath);
    expect(completed.frontmatter.status).toBe("Done");
  });
});

// ── Task lifecycle: archive ───────────────────────────────────────────────────

describe("task_archive lifecycle (filesystem)", () => {
  it("file moves from tasks/ to archive/ with reason in content", () => {
    const dir = makeTempProject();
    const srcPath = createTask(dir, "TASK-0001", "My Task");
    const task = readMarkdown<TaskFrontmatter>(srcPath);
    const archivePath = path.join(dir, IKE_DIR, DIRECTORIES.ARCHIVE, path.basename(srcPath));

    const content = `${task.content}\n\n**Archived:** duplicate`.trim();
    writeMarkdown(archivePath, task.frontmatter, content);
    fs.unlinkSync(srcPath);

    expect(fs.existsSync(srcPath)).toBe(false);
    expect(fs.existsSync(archivePath)).toBe(true);
    const archived = readMarkdown<TaskFrontmatter>(archivePath);
    expect(archived.content).toContain("duplicate");
  });
});

// ── Milestones ────────────────────────────────────────────────────────────────

describe("milestones", () => {
  it("nextMilestoneId returns MS-0001 for empty project", () => {
    const dir = makeTempProject();
    expect(nextMilestoneId(dir)).toBe("MS-0001");
  });

  it("increments milestone IDs", () => {
    const dir = makeTempProject();
    const fm: MilestoneFrontmatter = { id: "MS-0001", title: "First", status: "open", created: "2026-03-21" };
    writeMarkdown(milestonePath(dir, "MS-0001", "First"), fm, "");
    expect(nextMilestoneId(dir)).toBe("MS-0002");
  });

  it("findMilestoneFile returns null for nonexistent", () => {
    const dir = makeTempProject();
    expect(findMilestoneFile(dir, "MS-9999")).toBeNull();
  });

  it("milestonePath places file in milestones dir", () => {
    const dir = makeTempProject();
    const p = milestonePath(dir, "MS-0001", "Launch");
    expect(p).toContain(path.join(IKE_DIR, DIRECTORIES.MILESTONES));
    expect(path.basename(p)).toBe("MS-0001 - launch.md");
  });

  it("milestone close is idempotent", () => {
    const dir = makeTempProject();
    const fm: MilestoneFrontmatter = { id: "MS-0001", title: "Launch", status: "open", created: "2026-03-21" };
    const filePath = milestonePath(dir, "MS-0001", "Launch");
    writeMarkdown(filePath, fm, "");

    // Close once
    writeMarkdown(filePath, { ...fm, status: "closed" }, "notes");
    // Close again — same file, just overwrites
    writeMarkdown(filePath, { ...fm, status: "closed" }, "notes");
    const result = readMarkdown<MilestoneFrontmatter>(filePath);
    expect(result.frontmatter.status).toBe("closed");
  });
});

// ── Documents ─────────────────────────────────────────────────────────────────

describe("documents", () => {
  it("nextDocumentId returns DOC-0001 for empty project", () => {
    const dir = makeTempProject();
    expect(nextDocumentId(dir)).toBe("DOC-0001");
  });

  it("documentPath slugifies the title", () => {
    const dir = makeTempProject();
    const p = documentPath(dir, "DOC-0001", "Architecture Decision Record");
    expect(path.basename(p)).toBe("DOC-0001 - architecture-decision-record.md");
  });

  it("findDocumentFile returns null when docs dir is empty", () => {
    const dir = makeTempProject();
    expect(findDocumentFile(dir, "DOC-0001")).toBeNull();
  });

  it("listDocuments returns created documents", () => {
    const dir = makeTempProject();
    const fm: DocumentFrontmatter = { id: "DOC-0001", title: "Notes", created: "2026-03-21" };
    writeMarkdown(documentPath(dir, "DOC-0001", "Notes"), fm, "Some content");
    const docs = listDocuments(dir);
    expect(docs).toHaveLength(1);
    expect(docs[0].frontmatter.id).toBe("DOC-0001");
  });

  it("document append_content works correctly", () => {
    const dir = makeTempProject();
    const fm: DocumentFrontmatter = { id: "DOC-0001", title: "Notes", created: "2026-03-21" };
    const filePath = documentPath(dir, "DOC-0001", "Notes");
    writeMarkdown(filePath, fm, "Initial content");
    const doc = readMarkdown<DocumentFrontmatter>(filePath);
    const newContent = `${doc.content}\n\nAppended section`.trim();
    writeMarkdown(filePath, { ...fm, updated: "2026-03-21" }, newContent);
    const updated = readMarkdown<DocumentFrontmatter>(filePath);
    expect(updated.content).toContain("Initial content");
    expect(updated.content).toContain("Appended section");
  });
});
