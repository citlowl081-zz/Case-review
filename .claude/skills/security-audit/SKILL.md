---
name: security-audit
description: 代码安全审计 — 检查敏感信息泄漏、SQL注入、XSS、权限漏洞、不安全配置等安全风险
user-invocable: true
---

# 代码安全审计技能

你是安全审计专家。当用户输入 `/security-audit` 或请求安全检查时，按以下清单逐项审计。

## 六项安全检查

### 检查 1：敏感信息硬编码

扫描目标文件中是否直接写了：

| 危险模式 | 示例 |
|----------|------|
| API Key / Token | `api_key = "sk-xxx"`、`DASHSCOPE_API_KEY=sk-...` |
| 密码明文 | `password = "admin123"`、`ADMIN_PASSWORD = "123456"` |
| 数据库连接串（含密码） | `mysql://root:123456@localhost/db` |
| JWT 密钥 | `SECRET_KEY = "my-secret"` |
| 私钥/证书 | `-----BEGIN PRIVATE KEY-----` |
| 手机号/邮箱 | `phone = "13800138000"` |
| 内网 IP/域名 | `10.0.0.1`、`internal-api.company.com` |

**判断标准**：
- `.env` 和 `.env.example` 文件中如果 API Key 是真实值 → ❌ 高危
- `.env.example` 中如果是占位符（如 `sk-your-key-here`）→ ✅ 安全
- 代码中直接写死 → ❌ 高危

### 检查 2：SQL 注入风险

| 检查项 | 安全做法 | 危险做法 |
|--------|----------|----------|
| 查询方式 | ORM 参数化查询 | 字符串拼接 SQL |
| Python | `db.execute(select(User).where(User.id == uid))` | `cursor.execute(f"SELECT * FROM users WHERE id='{uid}'")` |
| 动态表名/列名 | 用白名单校验 | 直接拼接到 SQL |

**本项目用 SQLAlchemy ORM** → 天然防注入。重点检查是否有原生 SQL 拼接。

### 检查 3：配置文件中的明文敏感信息

扫描文件：`.env`、`.env.example`、`settings.json`、`config.py`、`*.yaml`

| 检查项 | 安全 | 危险 |
|--------|------|------|
| API Key | 放 `.env`（已 gitignore） | 放代码里、提交到 git |
| `.env.example` | 用占位符 `sk-your-key-here` | 放了真实 key |
| 数据库密码 | 用环境变量 | 写死在 `config.py` 里 |
| 管理员密码 | 首次登录强制修改 | 写死默认值且不要求修改 |

### 检查 4：权限控制漏洞

| 检查项 | 要确认的问题 |
|--------|-------------|
| 路由保护 | 每个需要登录的 API 是否都有 `Depends(get_current_user)`？ |
| 角色校验 | admin 专属接口是否有 `Depends(get_admin_user)`？ |
| 用户隔离 | 用户 A 能访问用户 B 的会话吗？ |
| IDOR 漏洞 | `DELETE /sessions/{id}` 是否校验了这个 session 属于当前用户？ |

### 检查 5：输入校验与注入

| 攻击类型 | 检查点 |
|----------|--------|
| 文件上传 | 是否校验了文件类型（白名单）、文件大小？ |
| 路径遍历 | 文件路径是否可能包含 `../` 跳出目录？ |
| 命令注入 | 是否有 `os.system(用户输入)`？ |
| XSS | 前端是否直接 `dangerouslySetInnerHTML` 用户输入？ |
| ReDoS | 正则是否有灾难性回溯风险？ |

### 检查 6：依赖与配置安全

| 检查项 | 说明 |
|--------|------|
| CORS 配置 | `allow_origins: ["*"]` 仅开发环境可用 |
| JWT 过期时间 | 不要太长（建议 ≤ 7 天） |
| 密码哈希 | 是否用 bcrypt（不是 MD5/SHA1）？ |
| Debug 模式 | 生产环境 `DEBUG=false` |
| HTTPS | 生产环境是否强制 HTTPS？ |
| 依赖版本 | `pip list` 检查是否有已知漏洞的旧版本 |

## 执行流程

### Step 1 — 确认范围

用户没说就默认检查当前打开的文件。如果用户说"全部检查"，则扫描整个项目。

### Step 2 — 读取代码

Read 目标文件，同时检查 `.env`、`config.py`、路由文件。

### Step 3 — 逐项审计

按六个检查项逐一分析，用 Grep 搜索危险模式：

```bash
# 搜索硬编码密钥
grep -rn "sk-" --include="*.py" --include="*.env"
grep -rn "password\s*=" --include="*.py"
grep -rn "SECRET_KEY" --include="*.py"

# 搜索 SQL 拼接
grep -rn "f\".*SELECT\|f\".*INSERT\|f\".*DELETE" --include="*.py"
grep -rn "\.execute(f" --include="*.py"

# 搜索不安全配置
grep -rn "DEBUG\s*=\s*True" --include="*.py"
grep -rn "allow_origins.*\*" --include="*.py"
```

### Step 4 — 输出报告

```
═══════════════════════════════════════════
        代 码 安 全 审 计 报 告
═══════════════════════════════════════════

📁 审计范围: backend/
🔍 发现问题: 8 个
   🔴 高危: 2    🟡 中危: 3    🟢 低危: 3

───────────────────────────────────────────
🔴 高危:
───────────────────────────────────────────
1. [敏感信息泄漏] backend/.env:6
   DASHSCOPE_API_KEY 包含真实 API Key
   建议: 确认 .env 已加入 .gitignore，且 .env.example 中为占位符

2. [敏感信息泄漏] backend/app/core/config.py:66
   ADMIN_PASSWORD 默认值为 "123456"
   建议: 首次登录后强制修改密码，或使用更复杂的默认密码

───────────────────────────────────────────
🟡 中危:
───────────────────────────────────────────
3. [配置安全] backend/app/core/config.py:13
   DEBUG=True 在生产环境应设为 False

4. [权限控制] backend/app/api/session.py:81
   DELETE /sessions/{id} 已校验用户归属 ✅

───────────────────────────────────────────
🟢 低危:
───────────────────────────────────────────
5. [依赖] bcrypt 3.2.2 版本较旧（最新 5.x），建议评估升级

───────────────────────────────────────────
📊 总评: B
  敏感信息已基本隔离在 .env 中，SQL 使用 ORM 无注入风险，
  但管理员默认密码需改善，DEBUG 模式需确认生产环境关闭。
═══════════════════════════════════════════
```

## 风险等级定义

| 等级 | 条件 |
|------|------|
| 🔴 高危 | 可直接导致数据泄漏、系统被入侵（明文密码、API Key 泄漏、SQL 注入） |
| 🟡 中危 | 在特定条件下可利用（权限绕过、不安全的默认配置、缺少输入校验） |
| 🟢 低危 | 最佳实践建议，暂无直接利用路径（依赖版本过旧、注释中的敏感信息） |

## 注意事项

- 检查 `.env` 时，只报告"是否已加入 .gitignore"和".env.example 是否安全"，不要输出完整密钥内容
- 本项目使用 SQLAlchemy ORM，天然防 SQL 注入，但仍需检查是否有裸 SQL 拼接
- Python 生态的常见漏洞：pickle 反序列化、eval/exec 动态执行、yaml.load (非 safe_load)
