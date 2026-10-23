# Luna Dimmer - Agent Guidelines & Engineering Directives

> [!CAUTION]
> ## 🚨 Mandatory Rules for AI Agents
>
> 1. **Do NOT run Git commit or push commands**:
>    - Agents and assistants are **strictly prohibited** from running `git commit`, `git push`, `git merge`, or modifying git history.
>    - **All Git commits, pushes, and staging must be manually executed by the user**.
>
> 2. **Do NOT write or run test scripts, compile, or package automatically**:
>    - **Strictly prohibited from writing or executing temporary test scripts** (such as `test_*.py`, reproduction scripts, or scratch test files).
>    - Do not trigger automated test suites, PyInstaller packaging (`build_exe.bat`), or build commands.
>    - **Directly locate the problem, edit the source code, and deliver immediately with maximum speed.** All tests, runs, and builds are performed manually by the user.
>
> 3. **Synchronize `docs/DESIGN.md` as Single Source of Truth**:
>    - Keep [`docs/DESIGN.md`](docs/DESIGN.md) synchronized whenever architecture, features, or design specifications change.
