# AI Gateway 全方位操作指南

## 📋 目录

1. [项目概述](#项目概述)
2. [系统架构](#系统架构)
3. [环境配置](#环境配置)
4. [安装部署](#安装部署)
5. [启动指南](#启动指南)
6. [功能说明](#功能说明)
7. [测试验证](#测试验证)
8. [API 端点](#api-端点)
9. [故障排除](#故障排除)
10. [高级配置](#高级配置)
11. [安全注意事项](#安全注意事项)
12. [维护监控](#维护监控)

---

## 项目概述

### 🎯 核心目标

AI Gateway 是一个本地影子内核，专门用于拦截和转发 Windsurf IDE 的 AI 请求，实现以下核心功能：

- **🔓 Premium 模式激活**: 绕过 IDE 内部的计费和限速锁
- **🎯 模型替换**: 自动将请求模型替换为高性能核心模型
- **🔄 双通道架构**: Agnes Merchant + Personal 双通道无缝切换
- **📡 流式转发**: 完整支持流式 AI 响应
- **🛡️ 优雅降级**: API 不可用时自动使用模拟响应

### 🚀 主要特性

| 特性 | 说明 | 状态 |
|------|------|------|
| Premium 模式 | 返回高级会员状态，绕过计费限制 | ✅ 已实现 |
| 无限速率 | 返回无限速率限制配置 | ✅ 已实现 |
| 模型替换 | 自动替换为 claude-3-5-sonnet | ✅ 已实现 |
| 双通道 | Merchant + Personal 50ms 切换 | ✅ 已实现 |
| 流式转发 | 完整 StreamingResponse 支持 | ✅ 已实现 |
| 端口自适应 | 优先 80 端口，冲突自动切换 8000 | ✅ 已实现 |

---

## 系统架构

### 🏗️ 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Windsurf IDE                             │
│  (AI 代码生成请求)                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              本地 Hosts 拦截 (codeium.com → 127.0.0.1)      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  AI Gateway (端口 80/8000)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  路由拦截层                                          │   │
│  │  • POST /v1/chat/completions                        │   │
│  │  • POST /exapi/chat/completions                     │   │
│  │  • GET /exapi/user/status                           │   │
│  │  • GET /exapi/config                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  模型替换层                                          │   │
│  │  • 强制替换为 claude-3-5-sonnet                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  双通道路由层                                        │   │
│  │  • 🚀 第一通道: Agnes Merchant Key                   │   │
│  │  • 🔄 第二通道: Agnes Personal Key (50ms 切换)      │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  流式转发层                                          │   │
│  │  • httpx.AsyncClient StreamingResponse             │   │
│  │  • 优雅降级到模拟响应                                │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Agnes API (api.agnes.ai)                     │
│  (实际 AI 模型推理)                                           │
└─────────────────────────────────────────────────────────────┘
```

### 🔄 请求流程

1. **拦截阶段**: Windsurf 发送请求到 codeium.com
2. **路由阶段**: Gateway 根据路径分发到不同处理器
3. **替换阶段**: 强制替换模型为 claude-3-5-sonnet
4. **通道选择**: 优先 Merchant，失败则切换 Personal
5. **转发阶段**: 流式转发到 Agnes API
6. **响应阶段**: 返回流式响应给 Windsurf

---

## 环境配置

### 🔧 系统要求

- **操作系统**: Windows 10/11
- **Python 版本**: Python 3.8+
- **内存**: 最低 2GB RAM
- **磁盘**: 最低 100MB 可用空间
- **网络**: 需要访问 Agnes API (api.agnes.ai)

### 📦 依赖包

```
fastapi>=0.104.0
uvicorn>=0.24.0
httpx>=0.25.0
pydantic>=2.0.0
python-dotenv>=1.0.0
requests>=2.31.0
```

### 🔐 环境变量配置

创建 `.env` 文件，配置以下环境变量：

```bash
# Agnes API 密钥 (必需)
AGNES_MERCHANT_KEY=your_merchant_key_here
AGNES_PERSONAL_KEY=your_personal_key_here
```

**配置说明**:
- `AGNES_MERCHANT_KEY`: Agnes 商户密钥，优先使用
- `AGNES_PERSONAL_KEY`: Agnes 个人密钥，备用通道

**获取密钥**:
1. 访问 Agnes 官方网站
2. 注册/登录账户
3. 在 API 设置中生成密钥
4. 分别获取 Merchant 和 Personal 密钥

### 🌐 Hosts 配置

编辑 `C:\Windows\System32\drivers\etc\hosts` 文件，添加以下内容：

```
127.0.0.1 codeium.com
127.0.0.1 www.codeium.com
127.0.0.1 api.codeium.com
```

**配置目的**: 将 Windsurf 的 AI 请求拦截到本地 Gateway

---

## 安装部署

### 📥 克隆项目

```bash
git clone https://github.com/bbaiwan657-max/ai-gateway-self-healing.git
cd ai-gateway-self-healing
```

### 🔨 安装依赖

```bash
pip install -r requirements.txt
```

**手动安装依赖** (如果没有 requirements.txt):

```bash
pip install fastapi uvicorn httpx pydantic python-dotenv requests
```

### ⚙️ 配置环境变量

1. 复制环境变量模板:
```bash
copy .env.example .env
```

2. 编辑 `.env` 文件，填入实际的 API 密钥:
```bash
notepad .env
```

3. 验证配置:
```bash
type .env
```

### 🧪 验证安装

```bash
python --version
pip list | findstr fastapi
pip list | findstr httpx
```

---

## 启动指南

### 🚀 标准启动

```bash
python main.py
```

**启动输出示例**:
```
============================================================
🚀 AI GATEWAY STARTING
============================================================
📡 Port: 80
🎯 Core Model: claude-3-5-sonnet
🔑 Merchant Channel: ✅ Active
🔑 Personal Channel: ✅ Active
🔓 Premium Mode: ✅ ENABLED
============================================================
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://127.0.0.1:80 (Press CTRL+C to quit)
```

### 🔌 端口说明

- **默认端口**: 80
- **备用端口**: 8000 (当 80 端口被占用时自动切换)
- **绑定地址**: 127.0.0.1 (仅本地访问)

**端口冲突处理**:
- 如果 80 端口被占用，系统会自动切换到 8000
- 控制台会显示端口切换提示
- 无需手动修改配置

### 🛑 停止服务

在运行终端按 `Ctrl+C` 停止服务

### 🔄 后台运行 (Windows)

**使用 start.bat**:
```bash
start.bat
```

**手动后台运行**:
```bash
start /B python main.py
```

---

## 功能说明

### 🔓 Premium 模式

**功能**: 返回高级会员状态，绕过 IDE 计费限制

**端点**: `GET /exapi/user/status`

**响应示例**:
```json
{
  "user_status": "active",
  "tier": "premium",
  "plan": "unlimited",
  "expires": "2099-12-31"
}
```

**效果**: Windsurf 认为用户是高级会员，不进行计费

### 🎯 模型替换

**功能**: 自动将请求中的模型替换为 claude-3-5-sonnet

**工作原理**:
1. 拦截 Windsurf 的模型请求 (如 gpt-4)
2. 强制替换为 claude-3-5-sonnet
3. 转发到 Agnes API

**示例**:
```python
# 原始请求
{
  "model": "gpt-4",
  "messages": [...]
}

# 实际转发
{
  "model": "claude-3-5-sonnet",
  "messages": [...]
}
```

### 🔄 双通道架构

**通道优先级**:
1. **第一通道**: Agnes Merchant Key
2. **第二通道**: Agnes Personal Key

**切换机制**:
- 第一通道失败后，50ms 内自动切换到第二通道
- 无缝切换，用户无感知
- 自动记录通道统计信息

**通道统计**:
```bash
GET /stats
```

**响应示例**:
```json
{
  "merchant": {"success": 10, "failures": 1},
  "personal": {"success": 2, "failures": 0}
}
```

### 📡 流式转发

**功能**: 完整支持流式 AI 响应

**实现**: 使用 httpx.AsyncClient 的 StreamingResponse

**优势**:
- 实时返回 AI 生成内容
- 降低首字延迟
- 提升用户体验

### 🛡️ 优雅降级

**功能**: Agnes API 不可用时自动使用模拟响应

**触发条件**:
- 网络连接失败
- API 密钥无效
- API 服务不可用

**降级响应**:
```json
{
  "id": "chatcmpl-merchant",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "claude-3-5-sonnet",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Mock response from merchant channel..."
    },
    "finish_reason": "stop"
  }]
}
```

---

## 测试验证

### 🧪 运行测试套件

```bash
python test_gateway.py
```

### 📊 测试项目

**TEST 1: Request Interception**
- 验证 Premium 模式激活
- 测试计费限制绕过

**TEST 2: Premium Config**
- 验证速率限制禁用
- 测试无限访问配置

**TEST 3: Channel Takeover**
- 验证 Agnes 通道接管流量
- 测试模型替换功能
- 检查通道统计信息

**TEST 4: EXAPI Endpoint**
- 验证 EXAPI 端点拦截
- 测试流式响应

### ✅ 测试通过标准

```
✅ Local shadow kernel is intercepting requests
✅ Premium mode activated - billing limits bypassed
✅ Rate limits disabled - unlimited access
✅ Agnes dual channels are handling traffic
✅ Model replacement working correctly

🎉 ALL TESTS PASSED - SYSTEM READY FOR WINDSURF!
```

### 🔍 手动测试

**测试 Premium 状态**:
```bash
curl http://127.0.0.1/exapi/user/status
```

**测试 Premium 配置**:
```bash
curl http://127.0.0.1/exapi/config
```

**测试聊天完成**:
```bash
curl -X POST http://127.0.0.1/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"Hello"}]}'
```

**测试通道统计**:
```bash
curl http://127.0.0.1/stats
```

---

## API 端点

### 📡 公开端点

#### 1. Premium 用户状态
```
GET /exapi/user/status
```

**响应**:
```json
{
  "user_status": "active",
  "tier": "premium",
  "plan": "unlimited",
  "expires": "2099-12-31"
}
```

#### 2. Premium 配置
```
GET /exapi/config
```

**响应**:
```json
{
  "user_status": "active",
  "tier": "premium",
  "rate_limit": {
    "requests_per_minute": 999999,
    "requests_per_day": 999999
  },
  "features": {
    "unlimited_coding": true,
    "priority_queue": true,
    "advanced_models": true
  }
}
```

#### 3. 聊天完成 (标准)
```
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "gpt-4",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "stream": true
}
```

#### 4. 聊天完成 (EXAPI)
```
POST /exapi/chat/completions
Content-Type: application/json

{
  "model": "gpt-4",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "stream": true
}
```

### 🔧 管理端点

#### 1. 健康检查
```
GET /health
```

**响应**:
```json
{
  "status": "healthy",
  "channels": {
    "merchant": {"success": 10, "failures": 1},
    "personal": {"success": 2, "failures": 0}
  },
  "core_model": "claude-3-5-sonnet"
}
```

#### 2. 通道统计
```
GET /stats
```

**响应**:
```json
{
  "merchant": {"success": 10, "failures": 1},
  "personal": {"success": 2, "failures": 0}
}
```

---

## 故障排除

### ❌ 常见问题

#### 1. 端口 80 被占用

**症状**:
```
⚠️  Port 80 is occupied, automatically switching to port 8000
```

**解决方案**:
- 系统会自动切换到 8000 端口
- 或手动释放 80 端口:
```bash
netstat -ano | findstr :80
taskkill /PID <进程ID> /F
```

#### 2. API 密钥无效

**症状**:
```
❌ [MERCHANT] Channel failed: 401 Unauthorized
```

**解决方案**:
- 检查 `.env` 文件中的密钥配置
- 验证密钥是否有效
- 重新生成 Agnes API 密钥

#### 3. 网络连接失败

**症状**:
```
❌ [MERCHANT] Channel failed: getaddrinfo failed
```

**解决方案**:
- 检查网络连接
- 验证 DNS 设置
- 检查防火墙设置
- 系统会自动降级到模拟响应

#### 4. 依赖包缺失

**症状**:
```
ModuleNotFoundError: No module named 'fastapi'
```

**解决方案**:
```bash
pip install -r requirements.txt
```

#### 5. Python 版本不兼容

**症状**:
```
SyntaxError: invalid syntax
```

**解决方案**:
- 确保使用 Python 3.8+
- 检查 Python 版本:
```bash
python --version
```

### 🔍 调试模式

**启用详细日志**:
编辑 `main.py`，修改日志级别:
```python
logging.basicConfig(
    level=logging.DEBUG,  # 改为 DEBUG
    ...
)
```

**查看日志文件**:
```bash
type gateway.log
```

**实时监控日志**:
```bash
Get-Content gateway.log -Wait -Tail 20
```

---

## 高级配置

### ⚙️ 自定义端口

编辑 `main.py`，修改端口检测逻辑:
```python
def get_available_port() -> int:
    # 自定义端口逻辑
    return 8080  # 固定使用 8080
```

### 🎯 修改核心模型

编辑 `main.py`，修改核心模型:
```python
CORE_MODEL = "claude-3-opus"  # 改为其他模型
```

### 🔄 调整切换延迟

编辑 `main.py`，修改通道切换延迟:
```python
await asyncio.sleep(0.1)  # 改为 100ms
```

### 📊 自定义响应

编辑 `main.py`，修改模拟响应:
```python
mock_response = {
    "id": f"chatcmpl-{channel_name}",
    "object": "chat.completion",
    "created": 1234567890,
    "model": CORE_MODEL,
    "choices": [{
        "index": 0,
        "message": {
            "role": "assistant",
            "content": "自定义响应内容"
        },
        "finish_reason": "stop"
    }]
}
```

### 🔐 添加认证

编辑 `main.py`，添加认证中间件:
```python
from fastapi import Header, HTTPException

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    auth_token = request.headers.get("Authorization")
    if auth_token != "your-secret-token":
        raise HTTPException(status_code=401, detail="Unauthorized")
    response = await call_next(request)
    return response
```

---

## 安全注意事项

### 🔒 安全最佳实践

1. **保护 API 密钥**
   - 永远不要将 `.env` 文件提交到 Git
   - 定期轮换 API 密钥
   - 使用强密钥生成器

2. **网络安全**
   - 仅绑定到 127.0.0.1 (本地)
   - 不要暴露到公网
   - 使用防火墙限制访问

3. **访问控制**
   - 添加认证机制
   - 限制访问频率
   - 监控异常访问

4. **日志安全**
   - 不要记录敏感信息
   - 定期清理日志文件
   - 保护日志文件权限

### 🛡️ 安全检查清单

- [ ] `.env` 文件在 `.gitignore` 中
- [ ] API 密钥已配置且有效
- [ ] 服务仅绑定到本地地址
- [ ] 防火墙规则已配置
- [ ] 日志不包含敏感信息
- [ ] 定期更新依赖包
- [ ] 监控系统运行状态

---

## 维护监控

### 📊 监控指标

**系统指标**:
- CPU 使用率
- 内存使用量
- 网络流量
- 端口状态

**业务指标**:
- 请求成功率
- 通道切换次数
- 平均响应时间
- 错误率

### 🔍 监控命令

**检查进程状态**:
```bash
tasklist | findstr python
```

**检查端口状态**:
```bash
netstat -ano | findstr :80
```

**检查日志**:
```bash
type gateway.log | findstr ERROR
```

**检查通道统计**:
```bash
curl http://127.0.0.1/stats
```

### 📈 性能优化

**优化建议**:
1. 使用 SSD 存储日志
2. 增加网络带宽
3. 优化日志级别
4. 使用连接池
5. 启用缓存

### 🔄 定期维护

**每日任务**:
- 检查系统日志
- 监控错误率
- 验证服务状态

**每周任务**:
- 清理旧日志文件
- 检查依赖更新
- 审查安全设置

**每月任务**:
- 轮换 API 密钥
- 更新依赖包
- 审查访问日志

---

## 📞 技术支持

### 🆘 获取帮助

- **GitHub Issues**: https://github.com/bbaiwan657-max/ai-gateway-self-healing/issues
- **文档**: 查看 README.md 和 SECURITY.md
- **日志**: 检查 gateway.log 获取详细错误信息

### 📚 相关资源

- **FastAPI 文档**: https://fastapi.tiangolo.com/
- **httpx 文档**: https://www.python-httpx.org/
- **Agnes API**: https://api.agnes.ai/docs

---

## 📝 更新日志

### v2.0.0 (2026-06-17)
- ✅ 完全重构系统架构
- ✅ 移除 guardian.py、nvidia、aws 逻辑
- ✅ 实现 Premium 模式激活
- ✅ 添加双通道架构
- ✅ 实现模型替换功能
- ✅ 添加流式转发支持
- ✅ 实现优雅降级机制
- ✅ 优化端口自适应
- ✅ 重写测试套件

### v1.0.0 (2026-06-16)
- ✅ 初始版本发布
- ✅ 基础网关功能
- ✅ 多提供商支持
- ✅ 安全检查集成

---

**最后更新**: 2026-06-17
**版本**: 2.0.0
**维护者**: bbaiwan657-max
