# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-05-13

### Changed
- **BREAKING: Package renamed from `ike-md` to `docket-md`.** Per visionlog ADR-003 in cockpit-eidos, the trilogy rebrand (`ike → docket`) lands as a full ecosystem rename, not a codename/brand split. PyPI package, GitHub repo, MCP tool prefix, dotfile dir, and all internal identifiers move from `ike*` to `docket*`.
- Python module: `ike_md/` → `docket_md/`
- Script entries: `ike-md` → `docket-md`, `ike-daemon` → `docket-daemon`
- MCP tool prefix: `mcp__ike__*` → `mcp__docket__*`
- Dotfile state directory: `.ike/` → `.docket/`, with `ike.json` → `docket.json`
- User config root: `~/.config/ike/` → `~/.config/docket/`
- launchd plist: `com.ike.daemon` → `com.docket.daemon`

### Removed
- TypeScript surface (the unpublished pre-port original at `src/`, `package.json`, `tsconfig.json`, `vitest.config.ts`). The Python port has been the published surface since 0.1.0; the TS source was a dead reference. Removing 5,838 lines.
- Migration scaffold at `refactor/` (one-shot used during the TS→Python port; port is complete).
- Empty `pypi-dev-workflow/` research scaffolding.

### Migration
- `ike-md` v0.3.0 ships as a deprecation-only release pointing at `docket-md`. PyPI doesn't allow name reuse, so `ike-md` remains permanently in its deprecated state.
- Existing projects with `.ike/` directories should rename to `.docket/` and edit `ike.json` → `docket.json` (rename file + change `ike_path` key to `docket_path` and `project` value if it referenced the brand).

## [0.1.0] - 2026-03-22

### Added
- Initial release
