import { describe, it, expect } from "vitest";
import { safePath } from "../security.js";
import * as path from "node:path";

describe("safePath", () => {
  const root = "/tmp/root";

  it("returns resolved path within root", () => {
    expect(safePath(root, "tasks", "TASK-0001.md")).toBe(
      path.resolve(root, "tasks", "TASK-0001.md")
    );
  });

  it("allows deeply nested paths", () => {
    expect(safePath(root, ".ike", "tasks", "TASK-0001.md")).toBe(
      path.resolve(root, ".ike", "tasks", "TASK-0001.md")
    );
  });

  it("throws on path traversal with ..", () => {
    expect(() => safePath(root, "..", "etc", "passwd")).toThrow(
      "Path traversal attempt"
    );
  });

  it("throws on deep traversal attempt", () => {
    expect(() => safePath(root, "tasks", "..", "..", "etc")).toThrow(
      "Path traversal attempt"
    );
  });

  it("handles single part", () => {
    expect(safePath(root, "ike.json")).toBe(path.resolve(root, "ike.json"));
  });
});
