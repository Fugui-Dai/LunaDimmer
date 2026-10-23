# Luna Dimmer - AI 协作与工程开发准则 (Project Directives)

> [!CAUTION]
> ## 🚨 核心禁令：Git 操作、测试脚本与构建打包绝对铁律
>
> 1. **严禁执行 Git 提交与推送（Strictly No Automated Git Commits/Pushes）**：
>    - **AI 助手与任何自动化脚本严禁执行 `git commit`、`git push`、`git branch`、`git merge`、`git rebase` 或改写版本历史的操作**。
>    - **所有代码的暂存、提交（Commit）与推送（Push）必须由用户亲自手动执行**。
>    - AI 仅负责在本地对文件进行精准编辑、分析与代码生成，修改完成后由用户审查并亲自提交到 Git 仓库。
>
> 2. **严禁编写测试脚本、运行测试与编译打包（Strictly No Automated Tests/Scratch Scripts/Builds）**：
>    - **严禁编写和执行任何临时测试脚本**（如 `test_*.py`、复现脚本、排查测试等），严禁做任何多余的测试脚本运行。
>    - **严禁擅自执行编译指令、运行自动化测试套件或执行 PyInstaller 等打包脚本**（如 `build_exe.bat`）。
>    - **直接定位核心问题、直接修改目标源码并迅速交付，杜绝拖沓慢速，追求最高响应速度**。所有的测试验证与打包完全由用户自行决定并在本地手动执行。
>
> 3. **设计总纲强制同步（Single Source of Truth）**：
>    - [`docs/DESIGN.md`](docs/DESIGN.md) 是本项目的技术总纲与白皮书。
>    - 任何涉及产品方向、核心算法、UI/UX 规范或底层架构的调整，必须第一时间同步更新 `docs/DESIGN.md`，确保白皮书与代码实现严格一致。
