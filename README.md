# HealMate-AI

> 你的专属 AI 健康管家，懂你的限制，陪你慢慢改变。

HealMate-AI 是一款基于大语言模型的个性化健康陪伴应用。通过对话式咨询收集用户的身体数据、生活习惯、厨房配置、过敏情况等信息，生成可执行的健康方案（饮食、饮水、睡眠、运动），并提供主动提醒、打卡反馈、困难安慰等功能。

## 核心特性

- 🧠 **深度个性化**：不仅知道你的身高体重，还了解你的过敏、厨具、买菜渠道、做饭时间、经济预算，所有方案都是你能做到的。
- 📋 **分层方案**：提供“理想版”“懒人版”“零成本版”，让任何状态的用户都能找到起点。
- 💚 **接纳失败**：中断时不责备，给予安慰，强调“重启比坚持更勇敢”。
- ⏰ **主动陪伴**：定时提醒、打卡反馈、情绪支持，形成“咨询→处方→执行→陪伴”完整闭环。

## 技术架构与栈

本项目采用严格的领域驱动设计 (DDD) 思想对目录进行了拆分：
- **前端展示**：`Streamlit` (位于 `src/pages/`)
- **服务层**：业务逻辑封装 (位于 `src/services/`)
- **数据访问层**：`SQLite` 本地存储 (位于 `src/repos/`)
- **核心模型**：上下文状态机与领域对象 (位于 `src/core/`)
- **AI 驱动**：`DeepSeek API`

## 快速开始

1. **克隆仓库**
   ```bash
   git clone https://github.com/czhlin/heal-mate-ai.git
   cd heal-mate-ai
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   - 复制一份 `.env.example`，将其重命名为 `.env`。
   - 在 `.env` 中填入你的 `DEEPSEEK_API_KEY`。

4. **运行应用**
   ```bash
   # 注意：入口文件已移动至 src 目录下
   streamlit run src/app.py
   ```

## 开发与测试

本项目配置了完善的自动化测试与代码规范检查机制：

- **运行测试**：项目使用 `pytest`，并在 `tests/` 目录下提供了基于临时内存数据库的隔离测试夹具。
  ```bash
  python -m pytest
  ```
- **代码规范**：项目使用 `ruff` 进行 Linter 和 Formatter 检查。
  ```bash
  python -m ruff check --fix .
  python -m ruff format .
  ```
- **AI 协作**：如果你使用 Cursor 或 Trae 进行开发，项目根目录已包含 `.cursorrules` 文件，AI 将自动遵守项目架构规范。详见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 路线图

- [x] MVP：基础表单 + AI处方生成
- [x] 对话式咨询与用户画像存储 (SQLite)
- [x] 分层方案（懒人版/零成本版）
- [x] 每日任务打卡与历史记录追踪
- [x] 困难模式与 AI 安慰反馈
- [ ] 体检报告上传与解读
- [ ] 专家服务与第三方可穿戴设备对接

## 贡献

欢迎 Issue 和 PR！本项目由 @czhlin 发起，期待与你一起打造有温度的 AI 健康管家。
在提交代码前，请务必阅读 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解我们的 Git Flow、Commit 规范和 AI 协作准则。

## 许可证

MIT
