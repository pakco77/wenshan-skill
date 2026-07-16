# Agent compatibility and GitHub distribution

## One canonical Skill

Publish one `knowledge-peak-map/` folder that follows the open [Agent Skills specification](https://agentskills.io/specification): `SKILL.md` at the root, with optional `scripts/`, `references/`, `assets/`, and `agents/`.

Do not maintain separate semantic implementations for Codex, Claude, Claude Code, CodeWhale, CodeBuddy, or WorkBuddy. Host-specific installation is only a thin adapter around the same GitHub folder.

## Recommended installation

The `skills` CLI can discover the nested Skill and ask which detected Agent should receive it:

```bash
npx skills add pakco77/wenshan-skill \
  --skill knowledge-peak-map \
  --global
```

List before installing:

```bash
npx skills add pakco77/wenshan-skill --list
```

For a non-interactive install to every supported Agent detected on the machine:

```bash
npx skills add pakco77/wenshan-skill \
  --skill knowledge-peak-map \
  --agent '*' \
  --global \
  --yes
```

If a host is not supported by the installer, clone the repository and copy or symlink the complete `knowledge-peak-map` folder into that host's recognized Skills directory.

## Host notes

| Host | Preferred route | Common manual location |
|---|---|---|
| Codex | `npx skills add ... --agent codex` or project install | `~/.codex/skills/knowledge-peak-map` |
| Claude Code | `npx skills add ... --agent claude-code` | `~/.claude/skills/knowledge-peak-map` |
| Claude | import the same Skill through the available Skills UI or workspace configuration | Host-version dependent |
| CodeWhale | `/skill install github:pakco77/wenshan-skill` or place it in a discovered Skills directory | project `.agents/skills/knowledge-peak-map`; global `~/.codewhale/skills/knowledge-peak-map` |
| CodeBuddy | install the same folder as a project or user Skill | project `.codebuddy/skills/knowledge-peak-map`; user `~/.codebuddy/skills/knowledge-peak-map` |
| WorkBuddy | import the GitHub Skill through its Skills interface | Do not assume an undocumented filesystem path |

CodeWhale documents GitHub Skill installation and discovery in its [official repository](https://github.com/Hmbown/CodeWhale). CodeBuddy documents project and user Skills in its [official CLI documentation](https://www.codebuddy.cn/docs/cli/skills). WorkBuddy's [official privacy documentation](https://www.workbuddy.ai/document/privacy-policy) confirms that third-party Skills can be installed, but does not define a stable public filesystem path.

## Runtime contract

- Python 3.10 or newer.
- Standard library only for the renderer and self-check.
- No vector database and no embedding dependency.
- The host Agent supplies semantic judgment; the renderer is deterministic.
- Read only the user-selected scope.
- Write derived files only under `Cognitive Map/Agent Atlas/`.
- Never place API keys, local absolute paths, or private article bodies into public repository assets.

## Release rule

Before tagging a release:

1. Run `python3 scripts/self_check.py`.
2. Run the Skill validator.
3. Generate Chinese and English demos from the same terrain JSON.
4. Confirm the opening asset contains synthetic/sample copy only.
5. Test repository discovery with `npx skills add pakco77/wenshan-skill --list`.
6. Record breaking schema changes in the commit and preserve legacy-field fallback for at least one release.
