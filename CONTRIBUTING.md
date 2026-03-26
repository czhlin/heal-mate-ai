# 贡献指南

感谢你对 HealMate AI 项目的关注！我们欢迎任何形式的贡献，包括但不限于提交 Bug、提出新功能建议、代码重构、文档更新等。

为了保证项目的代码质量和协作效率，请在提交代码前阅读以下指南。

## 1. 分支管理策略

本项目采用类似 Git Flow 的简化版分支管理策略：

- `main`: 主分支，保持稳定可用状态，所有发布版本均从这里打 Tag。**禁止直接 Push**。
- `dev`: 开发分支，日常新功能开发和 Bug 修复合并到此分支。
- `feature/*`: 功能分支，从 `dev` 检出，例如 `feature/add-login`。
- `fix/*`: 修复分支，从 `dev` 检出，例如 `fix/cookie-bug`。

### 工作流示例：

1. 从 `dev` 分支切出你的特性分支：
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature-name
   ```
2. 开发完成后，提交 Commit。
3. 推送到远程仓库，并在 GitHub 上向 `dev` 分支发起 Pull Request (PR)。
4. 代码审查通过后，由 Maintainer 合并到 `dev` 分支。

## 2. Commit 提交规范

本项目严格遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范。请使用中文编写提交说明。

格式如下：

```
<type>(<scope>): <subject>
```

### Type (必需)

- `feat`: 新增功能 (Feature)
- `fix`: 修复 Bug (Bugfix)
- `docs`: 仅修改文档 (Documentation)
- `style`: 格式化代码（不影响代码运行的变动，如空格、缩进等）
- `refactor`: 重构代码（既不修复 bug 也不添加新功能的代码修改）
- `perf`: 优化性能
- `test`: 增加或修改测试用例
- `chore`: 构建过程或辅助工具的变动
- `ci`: CI 配置文件和脚本的变动

### Scope (可选)

用于说明 commit 影响的范围，比如 `views`, `core`, `services`, `repos`, `ui` 等。

### Subject (必需)

简短描述变更的内容，使用中文。

**示例：**
- `feat(views): 新增日历打卡功能`
- `fix(core): 修复状态机状态流转错误`
- `refactor(services): 优化用户上下文数据结构`

## 3. Python 代码规范

本项目使用 [Ruff](https://docs.astral.sh/ruff/) 作为代码规范检查和格式化工具。

### 开发环境配置：

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 初始化 Pre-commit Hook（将在每次 Commit 前自动运行格式化和检查）：
   ```bash
   pre-commit install
   ```

### 编码风格要求：

- **类型提示 (Type Hints)**：核心逻辑和 Service 层的所有函数必须包含完整的类型提示（参数类型与返回值类型）。
- **中文注释**：对于复杂的业务逻辑、状态机流转、数据库操作等，必须添加架构师视角的中文注释，解释**为什么**这样做，而不仅仅是做什么。
- **模块化**：保持职责单一，避免在 `views/` 视图层写重度业务逻辑，应将其下沉到 `services/` 或 `core/` 层。

## 4. 提交 Pull Request

1. 在提交 PR 前，请确保代码已经过本地运行测试，并且 Ruff 检查通过（`pre-commit run --all-files`）。
2. PR 标题必须符合上述 Commit 规范（如 `feat: add user profile page`）。
3. 详细填写 PR 模板中的内容，说明修改了什么、为什么修改、如何测试等。

再次感谢你的贡献！
