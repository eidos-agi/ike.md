import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import * as fs from "node:fs";
import * as path from "node:path";
import matter from "gray-matter";

import {
  initProject,
  registerProject,
  resolveProject,
  listRegistered,
  loadConfig,
} from "./config.js";
import {
  listTasks,
  nextTaskId,
  taskPath,
  findTaskFile,
  readMarkdown,
  writeMarkdown,
  listMilestones,
  nextMilestoneId,
  milestonePath,
  listDocuments,
  nextDocumentId,
  documentPath,
  type TaskFrontmatter,
  type TaskStatus,
  type Priority,
  type DocumentFrontmatter,
} from "./files.js";

const INSTRUCTIONS = `ike.md is the execution forge — tasks, milestones, documents, Definition of Done. This is where work gets done.

Named for Eisenhower — the man who planned D-Day and then ran the free world. Ike didn't just plan. He executed at scale, across many agents, under time pressure, with contracts that had to be honored.

READ visionlog at the start of every session before touching anything. visionlog is the static St. Peter: it tells you where the ladder points, what the project has committed to, and what guardrails you must not cross. If a task would violate a visionlog guardrail, St. Peter has already told you no — adjust before you start.

Before making a consequential decision that spawns tasks, use research.md to earn that decision with evidence. Then record it in visionlog as an ADR. Then create tasks here to execute it.

The trilogy:
- research.md: decide with evidence
- visionlog: record vision, goals, guardrails, SOPs, ADRs — the contracts all execution must honor
- ike.md: execute within those contracts — this is where you are now

GUID workflow: Call project_set with the project path to register it and get its project_id. Pass that project_id to every subsequent tool call. For a new project, call project_init first.`;

function today(): string {
  return new Date().toISOString().split("T")[0];
}

function formatTask(t: ReturnType<typeof readMarkdown<TaskFrontmatter>>): string {
  const fm = t.frontmatter;
  const lines = [
    `## ${fm.id} — ${fm.title}`,
    `**Status:** ${fm.status}`,
    fm.priority ? `**Priority:** ${fm.priority}` : null,
    fm.milestone ? `**Milestone:** ${fm.milestone}` : null,
    fm.assignees?.length ? `**Assignees:** ${fm.assignees.join(", ")}` : null,
    fm.tags?.length ? `**Tags:** ${fm.tags.join(", ")}` : null,
    fm.dependencies?.length ? `**Depends on:** ${fm.dependencies.join(", ")}` : null,
    `**Created:** ${fm.created}`,
    fm.updated ? `**Updated:** ${fm.updated}` : null,
  ].filter(Boolean);

  if (fm["acceptance-criteria"]?.length) {
    lines.push("\n**Acceptance Criteria:**");
    fm["acceptance-criteria"].forEach((c) => lines.push(`- [ ] ${c}`));
  }

  if (fm["definition-of-done"]?.length) {
    lines.push("\n**Definition of Done:**");
    fm["definition-of-done"].forEach((d) => lines.push(`- [ ] ${d}`));
  }

  if (t.content) {
    lines.push("\n**Notes:**");
    lines.push(t.content);
  }

  return lines.join("\n");
}

export function createServer(): Server {
  const server = new Server(
    { name: "ike.md", version: "0.1.0" },
    {
      capabilities: { tools: {} },
      instructions: INSTRUCTIONS,
    }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [
      // ── Project management ──────────────────────────────────────────────────
      {
        name: "project_init",
        description: "Initialize a new ike.md project in a directory. Creates the .ike/ folder structure and ike.json with a stable GUID. Returns the project_id for use in all subsequent calls.",
        inputSchema: {
          type: "object",
          required: ["path"],
          properties: {
            path: { type: "string", description: "Absolute path to the project directory" },
            name: { type: "string", description: "Project name (defaults to directory name)" },
          },
        },
      },
      {
        name: "project_set",
        description: "Register an existing ike.md project for this session. Call this at session start. Returns the project_id (GUID) to use in all subsequent calls.",
        inputSchema: {
          type: "object",
          required: ["path"],
          properties: {
            path: { type: "string", description: "Absolute path to the project directory" },
          },
        },
      },
      {
        name: "project_list",
        description: "List all projects registered in this session.",
        inputSchema: { type: "object", properties: {} },
      },
      // ── Tasks ───────────────────────────────────────────────────────────────
      {
        name: "task_create",
        description: "Create a new task.",
        inputSchema: {
          type: "object",
          required: ["project_id", "title"],
          properties: {
            project_id: { type: "string", description: "Project GUID from project_set or project_init" },
            title: { type: "string" },
            description: { type: "string" },
            status: { type: "string", enum: ["To Do", "In Progress", "Draft"], default: "To Do" },
            priority: { type: "string", enum: ["high", "medium", "low"] },
            milestone: { type: "string", description: "Milestone ID (e.g. MS-0001)" },
            assignees: { type: "array", items: { type: "string" } },
            tags: { type: "array", items: { type: "string" } },
            dependencies: { type: "array", items: { type: "string" }, description: "Task IDs this depends on" },
            acceptance_criteria: { type: "array", items: { type: "string" } },
            definition_of_done: { type: "array", items: { type: "string" } },
          },
        },
      },
      {
        name: "task_list",
        description: "List tasks with optional filtering.",
        inputSchema: {
          type: "object",
          required: ["project_id"],
          properties: {
            project_id: { type: "string" },
            status: { type: "string", description: "Filter by status" },
            milestone: { type: "string", description: "Filter by milestone ID" },
            assignee: { type: "string" },
            tag: { type: "string" },
            include_completed: { type: "boolean", default: false },
          },
        },
      },
      {
        name: "task_view",
        description: "View a task in full detail by ID.",
        inputSchema: {
          type: "object",
          required: ["project_id", "task_id"],
          properties: {
            project_id: { type: "string" },
            task_id: { type: "string", description: "e.g. TASK-0001" },
          },
        },
      },
      {
        name: "task_edit",
        description: "Edit a task's fields. Only provided fields are updated.",
        inputSchema: {
          type: "object",
          required: ["project_id", "task_id"],
          properties: {
            project_id: { type: "string" },
            task_id: { type: "string" },
            title: { type: "string" },
            description: { type: "string" },
            status: { type: "string", enum: ["To Do", "In Progress", "Done", "Draft"] },
            priority: { type: "string", enum: ["high", "medium", "low"] },
            milestone: { type: "string" },
            assignees: { type: "array", items: { type: "string" } },
            tags: { type: "array", items: { type: "string" } },
            dependencies: { type: "array", items: { type: "string" } },
            acceptance_criteria: { type: "array", items: { type: "string" } },
            definition_of_done: { type: "array", items: { type: "string" } },
            append_notes: { type: "string", description: "Append text to the task's notes section" },
          },
        },
      },
      {
        name: "task_complete",
        description: "Mark a task as Done and move it to the completed folder.",
        inputSchema: {
          type: "object",
          required: ["project_id", "task_id"],
          properties: {
            project_id: { type: "string" },
            task_id: { type: "string" },
            notes: { type: "string", description: "Completion notes" },
          },
        },
      },
      {
        name: "task_archive",
        description: "Archive a task (cancelled, duplicate, or invalid).",
        inputSchema: {
          type: "object",
          required: ["project_id", "task_id"],
          properties: {
            project_id: { type: "string" },
            task_id: { type: "string" },
            reason: { type: "string" },
          },
        },
      },
      {
        name: "task_search",
        description: "Search tasks by keyword in title and description.",
        inputSchema: {
          type: "object",
          required: ["project_id", "query"],
          properties: {
            project_id: { type: "string" },
            query: { type: "string" },
            include_completed: { type: "boolean", default: false },
          },
        },
      },
      // ── Milestones ──────────────────────────────────────────────────────────
      {
        name: "milestone_create",
        description: "Create a new milestone.",
        inputSchema: {
          type: "object",
          required: ["project_id", "title"],
          properties: {
            project_id: { type: "string" },
            title: { type: "string" },
            description: { type: "string" },
            due: { type: "string", description: "Due date (YYYY-MM-DD)" },
          },
        },
      },
      {
        name: "milestone_list",
        description: "List all milestones.",
        inputSchema: {
          type: "object",
          required: ["project_id"],
          properties: {
            project_id: { type: "string" },
          },
        },
      },
      // ── Documents ───────────────────────────────────────────────────────────
      {
        name: "document_create",
        description: "Create a project document.",
        inputSchema: {
          type: "object",
          required: ["project_id", "title"],
          properties: {
            project_id: { type: "string" },
            title: { type: "string" },
            content: { type: "string" },
            tags: { type: "array", items: { type: "string" } },
          },
        },
      },
      {
        name: "document_list",
        description: "List all documents.",
        inputSchema: {
          type: "object",
          required: ["project_id"],
          properties: {
            project_id: { type: "string" },
          },
        },
      },
      {
        name: "document_view",
        description: "View a document by ID.",
        inputSchema: {
          type: "object",
          required: ["project_id", "document_id"],
          properties: {
            project_id: { type: "string" },
            document_id: { type: "string" },
          },
        },
      },
      {
        name: "document_update",
        description: "Update a document's content or tags. Only provided fields are changed.",
        inputSchema: {
          type: "object",
          required: ["project_id", "document_id"],
          properties: {
            project_id: { type: "string" },
            document_id: { type: "string" },
            title: { type: "string" },
            content: { type: "string" },
            tags: { type: "array", items: { type: "string" } },
            append_content: { type: "string", description: "Append text to existing content instead of replacing it" },
          },
        },
      },
    ],
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    const a = (args ?? {}) as Record<string, unknown>;

    try {
      switch (name) {
        // ── Projects ─────────────────────────────────────────────────────────
        case "project_init": {
          const config = initProject(a.path as string, a.name as string | undefined);
          guidToPathFix(config.id, path.resolve(a.path as string));
          return text(`Project initialized: **${config.project}**\nproject_id: \`${config.id}\`\nPath: ${a.path}\n\nUse this project_id in all subsequent calls.`);
        }

        case "project_set": {
          const result = registerProject(a.path as string);
          return text(`Project registered: **${result.project}**\nproject_id: \`${result.id}\`\n\nUse this project_id in all subsequent calls.`);
        }

        case "project_list": {
          const list = listRegistered();
          if (!list.length) return text("No projects registered this session. Call project_set with a project path.");
          return text(list.map((p) => `- \`${p.id}\` → ${p.path}`).join("\n"));
        }

        // ── Tasks ─────────────────────────────────────────────────────────────
        case "task_create": {
          const projectRoot = resolveProject(a.project_id);
          const id = nextTaskId(projectRoot);
          const title = a.title as string;
          const fm: TaskFrontmatter = {
            id,
            title,
            status: (a.status as TaskStatus) ?? "To Do",
            created: today(),
            ...(a.priority ? { priority: a.priority as Priority } : {}),
            ...(a.milestone ? { milestone: a.milestone as string } : {}),
            ...(a.assignees ? { assignees: a.assignees as string[] } : {}),
            ...(a.tags ? { tags: a.tags as string[] } : {}),
            ...(a.dependencies ? { dependencies: a.dependencies as string[] } : {}),
            ...(a.acceptance_criteria ? { "acceptance-criteria": a.acceptance_criteria as string[] } : {}),
            ...(a.definition_of_done ? { "definition-of-done": a.definition_of_done as string[] } : {}),
          };
          const filePath = taskPath(projectRoot, id, title);
          writeMarkdown(filePath, fm, (a.description as string) ?? "");
          return text(`Created **${id}** — ${title}\nStatus: ${fm.status}\nFile: ${filePath}`);
        }

        case "task_list": {
          const projectRoot = resolveProject(a.project_id);
          let tasks = listTasks(projectRoot, a.include_completed as boolean ?? false);
          if (a.status) tasks = tasks.filter((t) => t.frontmatter.status === a.status);
          if (a.milestone) tasks = tasks.filter((t) => t.frontmatter.milestone === a.milestone);
          if (a.assignee) tasks = tasks.filter((t) => t.frontmatter.assignees?.includes(a.assignee as string));
          if (a.tag) tasks = tasks.filter((t) => t.frontmatter.tags?.includes(a.tag as string));
          if (!tasks.length) return text("No tasks found.");
          return text(tasks.map((t) => {
            const fm = t.frontmatter;
            const badge = fm.status === "Done" ? "✓" : fm.status === "In Progress" ? "▶" : "○";
            const pri = fm.priority ? ` [${fm.priority}]` : "";
            return `${badge} **${fm.id}**${pri} — ${fm.title}`;
          }).join("\n"));
        }

        case "task_view": {
          const projectRoot = resolveProject(a.project_id);
          const filePath = findTaskFile(projectRoot, a.task_id as string);
          if (!filePath) return text(`Task ${a.task_id} not found.`);
          const task = readMarkdown<TaskFrontmatter>(filePath);
          return text(formatTask(task));
        }

        case "task_edit": {
          const projectRoot = resolveProject(a.project_id);
          const filePath = findTaskFile(projectRoot, a.task_id as string);
          if (!filePath) return text(`Task ${a.task_id} not found.`);
          const task = readMarkdown<TaskFrontmatter>(filePath);
          const fm = { ...task.frontmatter, updated: today() };
          if (a.title !== undefined) fm.title = a.title as string;
          if (a.status !== undefined) fm.status = a.status as TaskStatus;
          if (a.priority !== undefined) fm.priority = a.priority as Priority;
          if (a.milestone !== undefined) fm.milestone = a.milestone as string;
          if (a.assignees !== undefined) fm.assignees = a.assignees as string[];
          if (a.tags !== undefined) fm.tags = a.tags as string[];
          if (a.dependencies !== undefined) fm.dependencies = a.dependencies as string[];
          if (a.acceptance_criteria !== undefined) fm["acceptance-criteria"] = a.acceptance_criteria as string[];
          if (a.definition_of_done !== undefined) fm["definition-of-done"] = a.definition_of_done as string[];
          const content = a.append_notes
            ? `${task.content}\n\n${a.append_notes}`.trim()
            : a.description !== undefined ? a.description as string : task.content;
          writeMarkdown(filePath, fm, content);
          return text(`Updated **${fm.id}** — ${fm.title}`);
        }

        case "task_complete": {
          const projectRoot = resolveProject(a.project_id);
          const filePath = findTaskFile(projectRoot, a.task_id as string);
          if (!filePath) return text(`Task ${a.task_id} not found.`);
          const task = readMarkdown<TaskFrontmatter>(filePath);
          const fm = { ...task.frontmatter, status: "Done" as TaskStatus, updated: today() };
          const content = a.notes
            ? `${task.content}\n\n**Completion notes:** ${a.notes}`.trim()
            : task.content;
          const destPath = taskPath(projectRoot, fm.id, fm.title, true);
          writeMarkdown(destPath, fm, content);
          fs.unlinkSync(filePath);
          return text(`Completed **${fm.id}** — ${fm.title}\nMoved to completed/`);
        }

        case "task_archive": {
          const projectRoot = resolveProject(a.project_id);
          const filePath = findTaskFile(projectRoot, a.task_id as string);
          if (!filePath) return text(`Task ${a.task_id} not found.`);
          const task = readMarkdown<TaskFrontmatter>(filePath);
          const fm = { ...task.frontmatter, status: "Draft" as TaskStatus, updated: today() };
          const content = a.reason
            ? `${task.content}\n\n**Archived:** ${a.reason}`.trim()
            : task.content;
          const { safePath } = await import("./security.js");
          const { IKE_DIR, DIRECTORIES } = await import("./config.js");
          const archivePath = safePath(projectRoot, IKE_DIR, DIRECTORIES.ARCHIVE, path.basename(filePath));
          writeMarkdown(archivePath, fm, content);
          fs.unlinkSync(filePath);
          return text(`Archived **${fm.id}** — ${fm.title}`);
        }

        case "task_search": {
          const projectRoot = resolveProject(a.project_id);
          const query = (a.query as string).toLowerCase();
          const tasks = listTasks(projectRoot, a.include_completed as boolean ?? false);
          const matches = tasks.filter((t) =>
            t.frontmatter.title.toLowerCase().includes(query) ||
            t.content.toLowerCase().includes(query)
          );
          if (!matches.length) return text(`No tasks matching "${a.query}".`);
          return text(matches.map((t) => `**${t.frontmatter.id}** — ${t.frontmatter.title} [${t.frontmatter.status}]`).join("\n"));
        }

        // ── Milestones ────────────────────────────────────────────────────────
        case "milestone_create": {
          const projectRoot = resolveProject(a.project_id);
          const id = nextMilestoneId(projectRoot);
          const title = a.title as string;
          const fm = {
            id,
            title,
            status: "open" as const,
            created: today(),
            ...(a.due ? { due: a.due as string } : {}),
          };
          writeMarkdown(milestonePath(projectRoot, id, title), fm, (a.description as string) ?? "");
          return text(`Created milestone **${id}** — ${title}`);
        }

        case "milestone_list": {
          const projectRoot = resolveProject(a.project_id);
          const milestones = listMilestones(projectRoot);
          if (!milestones.length) return text("No milestones.");
          return text(milestones.map((m) => {
            const fm = m.frontmatter;
            const due = fm.due ? ` (due ${fm.due})` : "";
            return `${fm.status === "open" ? "○" : "✓"} **${fm.id}** — ${fm.title}${due}`;
          }).join("\n"));
        }

        // ── Documents ─────────────────────────────────────────────────────────
        case "document_create": {
          const projectRoot = resolveProject(a.project_id);
          const id = nextDocumentId(projectRoot);
          const title = a.title as string;
          const fm = {
            id,
            title,
            created: today(),
            ...(a.tags ? { tags: a.tags as string[] } : {}),
          };
          writeMarkdown(documentPath(projectRoot, id, title), fm, (a.content as string) ?? "");
          return text(`Created document **${id}** — ${title}`);
        }

        case "document_list": {
          const projectRoot = resolveProject(a.project_id);
          const docs = listDocuments(projectRoot);
          if (!docs.length) return text("No documents.");
          return text(docs.map((d) => `**${d.frontmatter.id}** — ${d.frontmatter.title}`).join("\n"));
        }

        case "document_view": {
          const projectRoot = resolveProject(a.project_id);
          const { safePath } = await import("./security.js");
          const { IKE_DIR, DIRECTORIES } = await import("./config.js");
          const dir = safePath(projectRoot, IKE_DIR, DIRECTORIES.DOCUMENTS);
          if (!fs.existsSync(dir)) return text("No documents found.");
          const match = fs.readdirSync(dir).find((f) => f.startsWith(a.document_id as string));
          if (!match) return text(`Document ${a.document_id} not found.`);
          const doc = readMarkdown<{ id: string; title: string; created: string }>(path.join(dir, match));
          return text(`## ${doc.frontmatter.id} — ${doc.frontmatter.title}\n\n${doc.content}`);
        }

        case "document_update": {
          const projectRoot = resolveProject(a.project_id);
          const { safePath } = await import("./security.js");
          const { IKE_DIR, DIRECTORIES } = await import("./config.js");
          const dir = safePath(projectRoot, IKE_DIR, DIRECTORIES.DOCUMENTS);
          if (!fs.existsSync(dir)) return text("No documents found.");
          const match = fs.readdirSync(dir).find((f) => f.startsWith(a.document_id as string));
          if (!match) return text(`Document ${a.document_id} not found.`);
          const filePath = path.join(dir, match);
          const doc = readMarkdown<DocumentFrontmatter>(filePath);
          const fm = { ...doc.frontmatter, updated: today() };
          if (a.title !== undefined) fm.title = a.title as string;
          if (a.tags !== undefined) fm.tags = a.tags as string[];
          const content = a.append_content
            ? `${doc.content}\n\n${a.append_content}`.trim()
            : a.content !== undefined ? a.content as string : doc.content;
          writeMarkdown(filePath, fm, content);
          return text(`Updated **${fm.id}** — ${fm.title}`);
        }

        default:
          return text(`Unknown tool: ${name}`);
      }
    } catch (err) {
      return text(`Error: ${err instanceof Error ? err.message : String(err)}`);
    }
  });

  return server;
}

// Workaround: expose guidToPath registration for project_init
function guidToPathFix(id: string, absPath: string): void {
  // project_init already writes config, but we need to register the GUID
  // Call registerProject after init writes the file
  try {
    registerProject(absPath);
  } catch {}
}

function text(content: string) {
  return { content: [{ type: "text" as const, text: content }] };
}

export async function startServer(): Promise<void> {
  const server = createServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
}
