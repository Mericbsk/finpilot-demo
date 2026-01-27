# Workspace Checklist

- [x] Verify that the `copilot-instructions.md` file in the `.github` directory is created.
- [x] Clarify project requirements (project type, language, framework).
- [x] Scaffold the project.
- [x] Customize the project to meet user requirements.
- [x] Install required extensions (none needed).
- [x] Compile the project (install dependencies, run diagnostics).
- [ ] Create and run a VS Code task if necessary (no task defined yet).
- [ ] Launch the project after confirming debug mode preference with the user.
- [x] Ensure documentation is complete (README + updated instructions).

## Execution Guidelines

**Progress Tracking**
- Use any available tools to manage the checklist above.
- Update the checklist after completing each step with a short summary.
- Review the current checklist status before starting a new step.

**Communication Rules**
- Keep messages concise; avoid long command outputs unless required.
- If a step is skipped, note that briefly (e.g., “No extensions needed”).
- Only explain project structure when asked.

**Development Rules**
- Work within the project root (`.`) unless instructed otherwise.
- Avoid adding external media or links unless explicitly requested.
- Use placeholders only when clearly marked for later replacement.
- Use the VS Code API tool exclusively for VS Code extension projects.
- Do not suggest reopening the workspace—it is already open in VS Code.
- Follow any additional setup information provided for the project.

**Folder Creation Rules**
- Treat the current directory as the project root.
- Ensure terminal commands run from `.` (use the appropriate path on Windows).
- Create new folders only when explicitly requested, except for `.vscode` when defining tasks.
- If a scaffold command requires a different folder name, ask the user to rename and reopen the workspace.

**Extension Installation Rules**
- Install only the extensions specified via `get_project_setup_info`.

**Project Content Rules**
- Default to a “Hello World” project only when requirements are unspecified.
- Avoid unnecessary integrations, links, or media assets.
- Make sure each generated component has a clear purpose.
- Ask for clarification before adding unconfirmed features.
- For VS Code extensions, consult the VS Code API documentation via the provided tool.

**Task Completion Rules**
- Project is considered complete when:
  - Scaffolding and compilation succeed without errors.
  - `.github/copilot-instructions.md` exists and is current.
  - `README.md` is present and up to date.
  - The user has clear instructions for debugging/launching the project.
- Update the plan before starting any new task.

- Work through each checklist item systematically.
- Keep communication concise and focused.
- Follow development best practices.
