/**
 * Golden fixture capture for ike.md TypeScript → Python migration.
 *
 * Calls every tool with representative inputs, records outputs + side effects.
 * Run: node refactor/capture-fixtures.mjs
 */

import { createServer } from "../dist/server.js";
import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";

const FIXTURES_DIR = path.join(import.meta.dirname, "fixtures");

async function callTool(server, name, args) {
  const handler = server._requestHandlers?.get("tools/call");
  if (!handler) throw new Error("No call handler");
  const result = await handler({
    method: "tools/call",
    params: { name, arguments: args },
  }, {});
  return result;
}

function snapshot(dir) {
  const files = {};
  function walk(d, prefix = "") {
    if (!fs.existsSync(d)) return;
    for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
      const rel = prefix ? `${prefix}/${entry.name}` : entry.name;
      if (entry.isDirectory()) {
        walk(path.join(d, entry.name), rel);
      } else {
        files[rel] = fs.readFileSync(path.join(d, entry.name), "utf-8");
      }
    }
  }
  walk(dir);
  return files;
}

function saveFixture(toolName, fixtureId, input, output, sideEffects) {
  const dir = path.join(FIXTURES_DIR, toolName);
  fs.mkdirSync(dir, { recursive: true });
  const fixture = {
    tool: toolName,
    fixture_id: fixtureId,
    input,
    output,
    side_effects: sideEffects,
    source_language: "typescript",
    captured_at: new Date().toISOString().split("T")[0],
  };
  fs.writeFileSync(
    path.join(dir, `${fixtureId}.json`),
    JSON.stringify(fixture, null, 2) + "\n"
  );
}

async function main() {
  const server = createServer();

  // Each test run gets a fresh temp dir
  let tmpDir;
  let projectId;

  function freshTmp() {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "ike-fixtures-"));
    return tmpDir;
  }

  // ── project_init ────────────────────────────────────────────────────────
  {
    const dir = freshTmp();
    const input = { path: dir, name: "test-project" };
    const output = await callTool(server, "project_init", input);
    const effects = snapshot(path.join(dir, ".ike"));
    saveFixture("project_init", "001-happy-path", input, output, { ike_dir: effects });

    // Extract project_id from output for subsequent calls
    const match = output.content[0].text.match(/project_id: `([^`]+)`/);
    projectId = match[1];
  }

  {
    const dir = freshTmp();
    const input = { path: dir };
    const output = await callTool(server, "project_init", input);
    const effects = snapshot(path.join(dir, ".ike"));
    saveFixture("project_init", "002-default-name", input, output, { ike_dir: effects });
  }

  {
    // Double init should return existing
    const dir = freshTmp();
    await callTool(server, "project_init", { path: dir, name: "first" });
    const input = { path: dir, name: "second" };
    const output = await callTool(server, "project_init", input);
    saveFixture("project_init", "003-idempotent", input, output, {});
  }

  // ── project_set ─────────────────────────────────────────────────────────
  {
    const dir = freshTmp();
    await callTool(server, "project_init", { path: dir, name: "set-test" });
    const input = { path: dir };
    const output = await callTool(server, "project_set", input);
    saveFixture("project_set", "001-happy-path", input, output, {});
  }

  {
    const input = { path: "/nonexistent/path" };
    const output = await callTool(server, "project_set", input);
    saveFixture("project_set", "002-no-project", input, output, {});
  }

  // ── project_list ────────────────────────────────────────────────────────
  {
    const output = await callTool(server, "project_list", {});
    saveFixture("project_list", "001-with-projects", {}, output, {});
  }

  // ── task_create ─────────────────────────────────────────────────────────
  // Use a fresh project for task tests
  const taskDir = freshTmp();
  const taskInitOutput = await callTool(server, "project_init", { path: taskDir, name: "task-tests" });
  const taskPid = taskInitOutput.content[0].text.match(/project_id: `([^`]+)`/)[1];

  {
    const input = { project_id: taskPid, title: "My First Task" };
    const output = await callTool(server, "task_create", input);
    const effects = snapshot(path.join(taskDir, ".ike/tasks"));
    saveFixture("task_create", "001-minimal", input, output, { tasks: effects });
  }

  {
    const input = {
      project_id: taskPid,
      title: "Full Task",
      description: "A detailed task",
      status: "In Progress",
      priority: "high",
      milestone: "MS-0001",
      assignees: ["daniel"],
      tags: ["urgent", "backend"],
      dependencies: ["TASK-0001"],
      acceptance_criteria: ["Tests pass", "Code reviewed"],
      definition_of_done: ["Merged to main", "Deployed"],
      visionlog_goal_id: "GOAL-001",
    };
    const output = await callTool(server, "task_create", input);
    const effects = snapshot(path.join(taskDir, ".ike/tasks"));
    saveFixture("task_create", "002-maximal", input, output, { tasks: effects });
  }

  {
    const input = { project_id: taskPid, title: "Draft Task", status: "Draft" };
    const output = await callTool(server, "task_create", input);
    saveFixture("task_create", "003-draft-status", input, output, {});
  }

  {
    const input = { project_id: taskPid, title: "café ñ 日本語 émojis 🚀" };
    const output = await callTool(server, "task_create", input);
    saveFixture("task_create", "004-unicode-title", input, output, {});
  }

  {
    const input = { project_id: "nonexistent-guid", title: "Should fail" };
    const output = await callTool(server, "task_create", input);
    saveFixture("task_create", "005-bad-project-id", input, output, {});
  }

  // ── task_list ───────────────────────────────────────────────────────────
  {
    const input = { project_id: taskPid };
    const output = await callTool(server, "task_list", input);
    saveFixture("task_list", "001-all-tasks", input, output, {});
  }

  {
    const input = { project_id: taskPid, status: "In Progress" };
    const output = await callTool(server, "task_list", input);
    saveFixture("task_list", "002-filter-status", input, output, {});
  }

  {
    const input = { project_id: taskPid, tag: "urgent" };
    const output = await callTool(server, "task_list", input);
    saveFixture("task_list", "003-filter-tag", input, output, {});
  }

  {
    const input = { project_id: taskPid, assignee: "daniel" };
    const output = await callTool(server, "task_list", input);
    saveFixture("task_list", "004-filter-assignee", input, output, {});
  }

  // ── task_view ───────────────────────────────────────────────────────────
  {
    const input = { project_id: taskPid, task_id: "TASK-0001" };
    const output = await callTool(server, "task_view", input);
    saveFixture("task_view", "001-exists", input, output, {});
  }

  {
    const input = { project_id: taskPid, task_id: "TASK-9999" };
    const output = await callTool(server, "task_view", input);
    saveFixture("task_view", "002-not-found", input, output, {});
  }

  // ── task_edit ───────────────────────────────────────────────────────────
  {
    const input = { project_id: taskPid, task_id: "TASK-0001", title: "Renamed Task", priority: "low" };
    const output = await callTool(server, "task_edit", input);
    const effects = snapshot(path.join(taskDir, ".ike/tasks"));
    saveFixture("task_edit", "001-update-fields", input, output, { tasks: effects });
  }

  {
    const input = { project_id: taskPid, task_id: "TASK-0001", append_notes: "Added some notes" };
    const output = await callTool(server, "task_edit", input);
    saveFixture("task_edit", "002-append-notes", input, output, {});
  }

  {
    const input = { project_id: taskPid, task_id: "TASK-0002", blocked_reason: "Waiting on API access" };
    const output = await callTool(server, "task_edit", input);
    saveFixture("task_edit", "003-set-blocked", input, output, {});
  }

  {
    const input = { project_id: taskPid, task_id: "TASK-0002", blocked_reason: "" };
    const output = await callTool(server, "task_edit", input);
    saveFixture("task_edit", "004-clear-blocked", input, output, {});
  }

  // ── task_complete ───────────────────────────────────────────────────────
  {
    const input = { project_id: taskPid, task_id: "TASK-0003", notes: "Done and dusted" };
    const output = await callTool(server, "task_complete", input);
    const effects = snapshot(path.join(taskDir, ".ike/completed"));
    saveFixture("task_complete", "001-with-notes", input, output, { completed: effects });
  }

  // ── task_search ─────────────────────────────────────────────────────────
  {
    const input = { project_id: taskPid, query: "Full" };
    const output = await callTool(server, "task_search", input);
    saveFixture("task_search", "001-match", input, output, {});
  }

  {
    const input = { project_id: taskPid, query: "zzzznonexistent" };
    const output = await callTool(server, "task_search", input);
    saveFixture("task_search", "002-no-match", input, output, {});
  }

  // ── milestone_create ────────────────────────────────────────────────────
  {
    const input = { project_id: taskPid, title: "v1.0 Release", description: "Ship it", due: "2026-06-01" };
    const output = await callTool(server, "milestone_create", input);
    saveFixture("milestone_create", "001-with-due", input, output, {});
  }

  {
    const input = { project_id: taskPid, title: "Stretch Goals" };
    const output = await callTool(server, "milestone_create", input);
    saveFixture("milestone_create", "002-minimal", input, output, {});
  }

  // ── milestone_list ──────────────────────────────────────────────────────
  {
    const input = { project_id: taskPid };
    const output = await callTool(server, "milestone_list", input);
    saveFixture("milestone_list", "001-with-milestones", input, output, {});
  }

  // ── milestone_view ──────────────────────────────────────────────────────
  {
    const input = { project_id: taskPid, milestone_id: "MS-0001" };
    const output = await callTool(server, "milestone_view", input);
    saveFixture("milestone_view", "001-exists", input, output, {});
  }

  // ── milestone_close ─────────────────────────────────────────────────────
  {
    const input = { project_id: taskPid, milestone_id: "MS-0002", notes: "Decided to skip" };
    const output = await callTool(server, "milestone_close", input);
    saveFixture("milestone_close", "001-with-notes", input, output, {});
  }

  // ── project_info ────────────────────────────────────────────────────────
  {
    const input = { project_id: taskPid };
    const output = await callTool(server, "project_info", input);
    saveFixture("project_info", "001-with-data", input, output, {});
  }

  // ── document_create ─────────────────────────────────────────────────────
  {
    const input = { project_id: taskPid, title: "Architecture Notes", content: "# Arch\n\nWe use microservices.", tags: ["architecture", "design"] };
    const output = await callTool(server, "document_create", input);
    saveFixture("document_create", "001-with-content", input, output, {});
  }

  {
    const input = { project_id: taskPid, title: "Empty Doc" };
    const output = await callTool(server, "document_create", input);
    saveFixture("document_create", "002-minimal", input, output, {});
  }

  // ── document_list ───────────────────────────────────────────────────────
  {
    const input = { project_id: taskPid };
    const output = await callTool(server, "document_list", input);
    saveFixture("document_list", "001-with-docs", input, output, {});
  }

  // ── document_view ───────────────────────────────────────────────────────
  {
    const input = { project_id: taskPid, document_id: "DOC-0001" };
    const output = await callTool(server, "document_view", input);
    saveFixture("document_view", "001-exists", input, output, {});
  }

  {
    const input = { project_id: taskPid, document_id: "DOC-9999" };
    const output = await callTool(server, "document_view", input);
    saveFixture("document_view", "002-not-found", input, output, {});
  }

  // ── document_update ─────────────────────────────────────────────────────
  {
    const input = { project_id: taskPid, document_id: "DOC-0001", content: "# Updated\n\nNew content." };
    const output = await callTool(server, "document_update", input);
    saveFixture("document_update", "001-replace-content", input, output, {});
  }

  {
    const input = { project_id: taskPid, document_id: "DOC-0001", append_content: "\n## Appendix\n\nMore stuff." };
    const output = await callTool(server, "document_update", input);
    saveFixture("document_update", "002-append-content", input, output, {});
  }

  // ── Count ───────────────────────────────────────────────────────────────
  let total = 0;
  for (const dir of fs.readdirSync(FIXTURES_DIR)) {
    const files = fs.readdirSync(path.join(FIXTURES_DIR, dir)).filter(f => f.endsWith(".json"));
    total += files.length;
    console.log(`  ${dir}: ${files.length} fixtures`);
  }
  console.log(`\nTotal: ${total} golden fixtures captured`);
}

main().catch(err => { console.error(err); process.exit(1); });
