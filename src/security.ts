import * as path from "node:path";

/**
 * Resolve a safe path within a root directory.
 * Prevents path traversal attacks.
 */
export function safePath(root: string, ...parts: string[]): string {
  const resolved = path.resolve(root, ...parts);
  if (!resolved.startsWith(path.resolve(root))) {
    throw new Error(`Path traversal attempt: ${parts.join("/")}`);
  }
  return resolved;
}
