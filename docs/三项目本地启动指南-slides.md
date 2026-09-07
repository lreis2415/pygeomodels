# ECG 项目本地调试指南（Frontend + GeoRAG + PyGeoModels MCP）

> 本文档将引导开发者在本地电脑上启动
> **Frontend（前端界面）**、**GeoRAG（RAG 问答后端）**、**PyGeoModels MCP（模型调用服务）**
> 三个项目，并让它们连接**远程的 ModelManager 和数据库服务**。

---

<!-- end_slide -->

## 1. 整体架构（先看懂这张图）

![架构图](image.png)
**本地项目：**

| 序号 | 项目 | 技术栈 | 作用 | GitHub |
|------|------|--------|------|--------|
| ① | PyGeoModels MCP | Python FastMCP | 把"模型列表/提交任务/查询进度"封装成 MCP 工具，供 GeoRAG 调用（本仓库） | https://github.com/lreis2415/pygeomodels |
| ② | GeoRAG | Python FastAPI + LangChain | 文档管理、向量库、RAG 智能问答；通过 MCP 协议调用地理模型 | https://github.com/lreis2415/GeoRAG |
| ③ | Frontend | React + TypeScript + UmiJS | 用户看到的网页界面：登录、模型管理、知识库、智能问答 | https://github.com/lreis2415/Frontend |

**连接的远程服务：**

| 远程服务 | 地址 | 谁连它 |
|----------|------|--------|
| modelmanager（模型管理器） | `http://8.130.184.170:31506` | Frontend（`/mbms/` 代理）和 PyGeoModels MCP（`modelmanager_url`） |
| 远程数据库 pgdb-geoagent | `8.130.184.170:30593`（库 `georag_dev`，用户 `geo`，密码 `123456`） | GeoRAG（`DB_URL`） |

> 数据流：你在浏览器登录（Frontend 从远程 modelmanager 拿到 JWT 令牌）→ 前端把
> `/llm` 请求转发给本地 GeoRAG → GeoRAG 校验令牌后，通过 MCP 调用本地 PyGeoModels 服务
> → PyGeoModels 再带同一个令牌去调用**远程 modelmanager** 执行地理模型任务。

---

<!-- end_slide -->

## 2. 准备工作（必须装的工具）

### 2.1 工具清单

| 工具 | 用途 | 安装方式 |
|------|------|----------|
| Git | 下载代码 | https://git-scm.com/downloads |
| Miniconda 或 Anaconda | Python 环境管理（两个 Python 项目各用一个环境） | https://docs.conda.io/en/latest/miniconda.html |
| Node.js 16（用 NVM 管理） | 运行 Frontend | 见下方 2.3 |
| Yarn | Frontend 依赖安装 | `npm i yarn -g` |
| Docker Desktop（可选） | 本地起 PostgreSQL 用（如果用远程数据库则可以不要） | https://www.docker.com/products/docker-desktop/ |

### 2.2 检查已安装

```bash
git --version          # 有输出即可
conda --version        # 有输出即可
```

<!-- end_slide -->

### 2.3 安装 Node.js 16 与 Yarn

**macOS / Linux**（用 NVM 管理 Node 版本）：

<!-- pause -->

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
# 重新打开终端，或执行：
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

nvm install 16
nvm use 16
nvm alias default 16      # 设为默认，避免以后忘记切换
```

**Windows**：安装 [nvm-windows](https://github.com/coreybutler/nvm-windows/releases)，然后：

<!-- pause -->

```bash
nvm install 16.20.2
nvm use 16.20.2
```

<!-- end_slide -->

验证并安装 Yarn：

<!-- pause -->

```bash
node --version    # 应输出 v16.x.x
npm i yarn -g
yarn --version
```

### 2.4 准备远程服务的访问凭证

- **ModelManager 登录账号**：在前端注册一个后，联系管理员申请升级权限，否则无法运行模型。
- **阿里云百炼 API Key（OpenAI 兼容）**：GeoRAG 的 LLM / Embedding 都走阿里云百炼
  （`https://dashscope.aliyuncs.com/compatible-mode/v1`），需要到
  [阿里云百炼控制台](https://bailian.console.aliyun.com/) 申请一个 `sk-...` 的 API Key。使用免费模型额度即可。
<!-- pause -->
- **JWT 公钥 `public.pem`**：GeoRAG 校验登录令牌需要 `.secrets/jwt/public.pem`（该文件被
  git 忽略，不会随代码下载），向团队同事拷贝一份放到
  `GeoRAG/.secrets/jwt/public.pem`。如果暂时拿不到，可以先用第 6.4 节的"调试模式"
  （`AUTH_ENABLED=false`）跑起来。

---

<!-- end_slide -->

## 3. 获取代码（三个仓库）

在你想放代码的目录下（例如 `~/Desktop/EGC`）执行：

<!-- pause -->

```bash
git clone git@github.com:lreis2415/pygeomodels.git
git clone git@github.com:lreis2415/GeoRAG.git
git clone git@github.com:lreis2415/Frontend.git
```

> 如果还没配置 GitHub SSH 密钥，也可以用 HTTPS 地址：
> `git clone https://github.com/lreis2415/xxx.git`。
> 另外 Frontend 请切换到开发分支：`cd Frontend && git checkout dev`。

本文档后面提到的路径以这三个目录名为准（下文简称"项目根目录"）。

---

<!-- end_slide -->

## 4. 启动顺序与端口总览

**强烈建议按下面的顺序启动**（后面项目依赖前面项目的端口）：

| 步骤 | 项目 | 本地端口 | 关键地址 |
|------|------|----------|----------|
| 第 1 步 | PyGeoModels MCP | `8050` | `http://127.0.0.1:8050/mcp` |
| 第 2 步 | GeoRAG | `7512` | `http://localhost:7512/docs` |
| 第 3 步 | Frontend | `8000` | `http://localhost:8000` |

> Frontend 通过 `localhost:7512` 找 GeoRAG；GeoRAG 通过 `localhost:8050/mcp` 找 PyGeoModels MCP。

---

<!-- end_slide -->

## 5. 第 1 步：启动 PyGeoModels MCP 服务

> 需要 Python 3.11，建议用 conda 单独建一个环境，避免污染系统 Python。

### 5.1 创建环境并安装依赖

```bash
cd pygeomodels

# 创建并激活 conda 环境
conda create -n pygeomodels python=3.11 -y
conda activate pygeomodels

# 升级 pip 并安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 以开发模式安装本项目
pip install -e .
```

> `requirements.txt` 里有 pygeoc 等地理库，安装时间较长，耐心等待即可。
> **GDAL 不是必需依赖**：MCP 服务的模型管理（EGC）/AOI 工具都不需要它；只有启用
> "地形分析工具"（见下方 5.2 的 `enable_terrain_analysis_tools`）时才需要额外安装：
> `pip install "GDAL>=3.0.0"`。
> 安装失败时，多半是网络问题，可换用国内镜像：
> `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

<!-- end_slide -->

### 5.2 配置：指向远程 modelmanager

本项目通过 `pygeomodels/pygeomodels/default_config.ini` + `local_config.ini` 两级配置。
`local_config.ini` 会被优先加载，且不会被 git 提交。

复制模板并编辑：

<!-- pause -->

```bash
cp pygeomodels/local_config.ini.example pygeomodels/local_config.ini
```

用任意文本编辑器打开 `pygeomodels/local_config.ini`，确保包含以下内容
（**重点是把 modelmanager 指到远程地址**）：

<!-- pause -->

```ini
[FEATURE_FLAGS]
enable_terrain_analysis_tools = false    # 地形分析工具（可选：需先安装 GDAL 才能设为 true）
enable_model_management_tools = true     # 模型管理工具（必须为 true）
enable_aoi_tools = true                  # AOI 研究区工具

# 本地测试令牌：如果暂时没有有效令牌，留空即可；
# 有令牌时填在这里，避免每次请求都手动带 Authorization 头
test_bearer_token =

[SERVICE]
# 远程 modelmanager 地址（关键配置）
modelmanager_url = http://8.130.184.170:31506
```

> GDAL 是可选的：默认配置下 MCP 服务的模型管理/AOI 工具都不需要 GDAL；
> 只有把 `enable_terrain_analysis_tools` 设为 `true` 时才需要预先安装 GDAL
> （`pip install "GDAL>=3.0.0"`），否则启动时会跳过地形工具并给出提示，不影响其他功能。

> `default_config.ini` 中默认的 `modelmanager_url = http://localhost:7504` 是给本地
> 自建 modelmanager 用的；**连接远程服务时必须在 `local_config.ini` 里覆盖为
> `http://8.130.184.170:31506`**。

<!-- end_slide -->

### 5.3 启动服务

```bash
conda activate pygeomodels
python pygeomodels_service.py
```

看到类似日志即成功：

<!-- pause -->

```
Uvicorn running on http://127.0.0.1:8050
```

<!-- end_slide -->

### 5.4 验证

新开一个终端：

<!-- pause -->

```bash
curl -i http://127.0.0.1:8050/mcp -m 5
```

能返回 HTTP 响应（不是 `Connection refused`）即服务正常。**请保持此终端窗口运行**，
不要关闭。

> 提示：`pygeomodels_service.py` 提供 `GET /mcp`（MCP streamable_http 端点）。
> 直接调用工具需要带 `Authorization: Bearer <JWT>` 请求头；没有令牌时，
> `list_categories` 等工具会报 "Missing Bearer token"，这是正常的，见第 9 节 FAQ。

---

<!-- end_slide -->

## 6. 第 2 步：启动 GeoRAG

> 需要 Python 3.9+（推荐 3.11），同样建议独立 conda 环境（默认名 `langchain_v03`）。

### 6.1 创建环境并安装依赖

```bash
cd GeoRAG

conda create -n langchain_v03 python=3.11 -y
conda activate langchain_v03
pip install -r requirements.txt
```

<!-- end_slide -->

### 6.2 配置 `.env`（核心步骤）

```bash
cp .env.example .env
```

编辑 `.env`，对照下面的模板逐项确认：

<!-- pause -->

```bash
# ---------- LLM / Embedding 服务（远程，走阿里云百炼 OpenAI 兼容接口） ----------
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-你的阿里云百炼APIKey
EMBEDDING_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# ---------- 数据库：连远程 pgdb-geoagent（关键配置） ----------
APP_ENV=local
DB_URL=postgresql+psycopg://geo:123456@8.130.184.170:30593/georag_dev

# ---------- 认证 ----------
JWT_PUBLIC_KEY_PATH=.secrets/jwt/public.pem
AUTH_ENABLED=true            # 有 public.pem 时保持 true；拿不到就改 false 调试
AUTH_DEBUG_USER_ID=local-debug-user   # 仅 AUTH_ENABLED=false 时生效

# ---------- 向量库 ----------
USE_PGVECTOR=true
DEFAULT_EMBEDDING_MODEL=text-embedding-v4
VECTOR_DIMENSION=1536

# ---------- MCP 配置：指向本地 PyGeoModels MCP 服务（关键配置） ----------
MCP_CONFIG={"pygeomodels": {"url": "http://localhost:8050/mcp", "transport": "streamable_http"}}

# ---------- 一键启动脚本用的 conda 环境名 ----------
GEORAG_CONDA_ENV=langchain_v03
```

<!-- end_slide -->

**要点：**

- `DB_URL` 的 `8.130.184.170:30593` 是**远程 pgdb-geoagent**（库 `georag_dev`，
  用户 `geo`，密码 `123456`）。不想用远程库时，也可以用本地 Docker 起一个一模一样的库
  （见 6.5），两者凭据相同。
- `MCP_CONFIG` 里的 `http://localhost:8050/mcp` 必须和 PyGeoModels MCP 的端口一致，
  否则 GeoRAG 里的"智能体调用模型"功能会失败。

### 6.3 放好 JWT 公钥

```bash
# 把团队提供的 public.pem 放到（目录不存在就先创建）：
# GeoRAG/.secrets/jwt/public.pem
mkdir -p .secrets/jwt
# 然后把 public.pem 拷贝进去，例如：
# cp ~/Downloads/public.pem .secrets/jwt/
```

<!-- end_slide -->

### 6.4 启动服务

```bash
conda activate langchain_v03
python main.py
```

看到 `Uvicorn running on http://0.0.0.0:7512` 即成功。

<!-- end_slide -->

### 6.5 验证

新开终端：

<!-- pause -->

```bash
curl http://localhost:7512/llm/v1/health
```

返回健康信息即正常。浏览器打开 <http://localhost:7512/docs> 能看到 Swagger 接口文档。
**保持此终端运行。**

<!-- end_slide -->

> **（可选）用本地 Docker 数据库替代远程库**：如果你连不上远程 30593 端口，
> 也可以在 GeoRAG 目录下用 Docker 起本地 pgvector 库（凭据与远程完全一致）：

```bash
docker compose up -d postgres     # 本地库地址 localhost:5434
# 验证扩展
docker exec -it georag-postgres psql -U geo -d georag_dev -c "SELECT extname FROM pg_extension WHERE extname='vector';"
```

> 此时 `.env` 中把 `DB_URL` 改成：
> `postgresql+psycopg://geo:123456@localhost:5434/georag_dev`
>
> 本项目自带一键启动脚本 `./start-mac.sh`（macOS/Linux）或 `start-win.bat`（Windows），
> 它会自动激活 conda 环境、检查依赖、拉起数据库并启动服务，也可以直接用。

---

<!-- end_slide -->

## 7. 第 3 步：启动 Frontend

> 需要 Node.js 16 + Yarn（见 2.3 节）。

### 7.1 安装依赖

```bash
cd Frontend
git checkout dev       # 切到开发分支

nvm use 16             # 确认 Node 版本
yarn                   # 安装依赖（会自动生成 Umi 临时文件）
```

<!-- end_slide -->

### 7.2 配置 `.env`（核心步骤）

```bash
cp .env.example .env
```

编辑 `.env`，确认下面几项：

<!-- pause -->

```bash
# ---------- 底图密钥（如已配置可不动） ----------
UMI_APP_MAPTILER_KEY=你的MapTiler密钥
UMI_APP_GOOGLE_MAP_TILES_KEY=你的Google地图密钥

# ---------- 后端代理地址（关键配置） ----------
MBMS_PROXY_TARGET=http://8.130.184.170:31506   # 远程 modelmanager（关键）
CODEENV_PROXY_TARGET=http://47.243.118.35:7600 # 远程编程建模后端
LLM_PROXY_TARGET=http://localhost:7512         # 本地 GeoRAG（关键）
V2_PROXY_TARGET=http://127.0.0.1:4523/m1/4312392-3955120-default/  # 建模服务 Mock
```

**要点：** `MBMS_PROXY_TARGET` 必须指向远程 modelmanager
（`http://8.130.184.170:31506`），这样前端的登录、模型管理请求才会打到远程服务；
`LLM_PROXY_TARGET` 指向本地 GeoRAG（`localhost:7512`），问答功能才会走本地 RAG。

<!-- end_slide -->

### 7.3 启动

```bash
yarn dev        # 完整系统；只想用问答模块可运行 yarn dev:aichat
```

看到 `App listening at http://localhost:8000` 即成功。

### 7.4 验证

浏览器打开 <http://localhost:8000>，跳到登录页即成功。**保持此终端运行。**

---

<!-- end_slide -->

## 8. 端到端验证清单（启动完必做）

三个终端窗口分别跑着三个服务后，按顺序验证：

| # | 检查项 | 方法 | 预期 |
|---|--------|------|------|
| 1 | MCP 服务在线 | `curl -i http://127.0.0.1:8050/mcp -m 5` | 返回 HTTP 响应 |
| 2 | GeoRAG 健康 | `curl http://localhost:7512/llm/v1/health` | 返回健康 JSON |
| 3 | GeoRAG 连上远程库 | GeoRAG 启动日志无数据库报错 | 无 `connection refused` |
| 4 | Frontend 打开 | 浏览器访问 `http://localhost:8000` | 显示登录页 |

<!-- pause -->

| # | 检查项 | 方法 | 预期 |
|---|--------|------|------|
| 5 | 登录成功 | 用 modelmanager 账号登录 | 能进主界面 |
| 6 | 模型列表加载 | 打开"模型管理/官方模型库" | 能看到远程 modelmanager 的模型列表 |
| 7 | 知识库问答 | 打开 AiChat → 智能问答，上传文档后提问 | 能基于 RAG 回答 |
| 8 | 调用地理模型 | 在问答/实验模式中让智能体执行模型任务 | 任务状态能查询到（需要 MCP 链路 5.4 正常） |

如果第 5 步登录就失败，多半是 `MBMS_PROXY_TARGET` 配错或网络不通；
如果第 6 步模型列表为空，检查 PyGeoModels MCP 的 `modelmanager_url` 和令牌（见 FAQ）。

---

<!-- end_slide -->

## 9. 常见问题（FAQ）

### Q1：调用 MCP 工具报 "Missing Bearer token"？

PyGeoModels MCP 需要 JWT 令牌。三种解决方式：

1. 走正常链路：通过 Frontend 登录后，GeoRAG 会自动把用户令牌透传给 MCP 服务，不需要手动配置；
2. 本地调试：把令牌填到 `local_config.ini` 的 `test_bearer_token`；
<!-- pause -->
3. 手动验证：请求时带 `Authorization: Bearer <令牌>` 请求头。

### Q2：GeoRAG 提示连接远程数据库失败 / `connection refused`？

- 检查远程库端口是否可达：`nc -z 8.130.184.170 30593`（Windows 可用 PowerShell 的 `Test-NetConnection`）；
- 检查 `.env` 的 `DB_URL` 是否写对（用户 `geo`、密码 `123456`、库 `georag_dev`）；
<!-- pause -->
- 实在连不上，改用 6.5 节的本地 Docker 数据库。

### Q3：前端登录提示 401 / 502？

- 确认 `MBMS_PROXY_TARGET=http://8.130.184.170:31506` 且该地址可访问：
  `curl -i http://8.130.184.170:31506/mbms/v1/...`（返回 401 是正常的，说明服务在线）；
- 检查 Frontend 的 `yarn dev` 终端是否有代理报错日志。

<!-- end_slide -->

### Q4：端口被占用？

- `lsof -i :8050` / `lsof -i :7512` / `lsof -i :8000`（Windows 用
  `netstat -ano | findstr 端口`），找到占用进程结束掉，或改项目端口配置。

### Q5：GeoRAG 启动报 `public.pem` 找不到 / JWT 校验失败？

- 该文件被 git 忽略，需从团队拷贝到 `GeoRAG/.secrets/jwt/public.pem`；
- 本地调试可临时把 `AUTH_ENABLED=false`（同时设置 `AUTH_DEBUG_USER_ID`），
  注意**不要**在公网环境关闭认证。

### Q6：`pip install` / `yarn` 很慢或失败？

- pip 加国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`；
- yarn 可配置镜像：`yarn config set registry https://registry.npmmirror.com`；
<!-- pause -->
- 重试一次往往也能解决。

<!-- end_slide -->

### Q7：`yarn dev` 报 Node 版本不兼容？

Frontend 要求 Node 16，务必先 `nvm use 16` 再 `yarn dev`。

### Q8：GeoRAG 里"智能体"功能不可用 / 找不到 MCP 工具？

- 确认 PyGeoModels MCP（端口 8050）已启动；
- 确认 GeoRAG `.env` 的 `MCP_CONFIG` 里 url 为 `http://localhost:8050/mcp`、
  transport 为 `streamable_http`；
<!-- pause -->
- 重启 GeoRAG 让配置生效，看启动日志里是否打印"已连接 N 个服务器"。

---

<!-- end_slide -->

## 附：常用命令速查

<!-- column_layout: [1, 1] -->
<!-- column: 0 -->

```bash
# PyGeoModels MCP（终端 1）
conda activate pygeomodels && cd pygeomodels && python pygeomodels_service.py

# GeoRAG（终端 2）
conda activate langchain_v03 && cd GeoRAG && python main.py

# Frontend（终端 3）
cd Frontend && nvm use 16 && yarn dev
```

<!-- column: 1 -->

| 需要验证的东西 | 命令 |
|----------------|------|
| 远程 modelmanager 在线 | `curl -i http://8.130.184.170:31506/` |
| 远程数据库可达 | `nc -z 8.130.184.170 30593` |
| MCP 服务在线 | `curl -i http://127.0.0.1:8050/mcp -m 5` |
| GeoRAG 健康 | `curl http://localhost:7512/llm/v1/health` |

<!-- reset_layout -->
