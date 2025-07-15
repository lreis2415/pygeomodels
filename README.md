
## Install pygeomodels

pygeomodels处在不断开发完善中，请根据如下命令安装最新开发版本。

```bash
pip install git+https://github.com/lreis2415/pygeomodels
```

或者：
```bash
git clone https://github.com/lreis2415/pygeomodels
cd pygeomodels
# For *nix OS
sudo ./reinstall.sh
# For Windows, open a cmd windows as Administrator
./reinstall.bat
# You can specific the Python path, e.g.,
./reinstall.bat D:\demo\python36
```

## 主要功能

`pygeomodels` 是一个用于与 "OneSIS" 地理模型服务进行交互的 Python 库。其核心功能包括：

1.  **认证**: 使用 Keycloak 处理服务认证，为 API 请求获取不记名令牌 (`config.py`)。
2.  **模型发现**: `modelBank` 类连接到模型管理器端点，获取可用的地理空间模型目录，包括模型列表及其元数据。
3.  **动态模型执行**: `modelCaller` 类提供了一个强大而直观的模型运行界面。它会根据可用的模型动态生成相应的方法（例如，如果存在 "pitRemove" 模型，您可以通过 `caller.pitRemove(...)` 来调用它）。这使得该库能够适应服务上可用的任何模型。
4.  **任务提交**: 调用模型函数时, `modelCaller` 会构建并向服务器的 API 发送请求，以启动一个新的建模任务，并传递所需的输入/输出数据路径和参数。
5.  **任务管理**: `modelTask` 类允许与已提交的任务进行交互。给定任务的 `project_id`，它可以用于检索日志、检查进度、停止或删除任务。
6.  **配置**: 该库通过一个 `.ini` 文件 (`default_config.ini`) 进行配置，其中指定了服务 URL、API 路由和认证详细信息。
