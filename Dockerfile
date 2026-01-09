# PyGeoModels MCP 服务 Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（包括 pygeoc 编译所需的依赖）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        gdal-bin \
        libgdal-dev \
        && rm -rf /var/lib/apt/lists/*

# 先只复制 requirements.txt，这样依赖变化才会重新安装
COPY requirements.txt .

# 安装 Python 依赖（这层会被缓存，除非 requirements.txt 变化）
RUN pip install --upgrade pip && \
    pip install wheel && \
    pip install -r requirements.txt

# 再复制项目文件（代码变化不会影响上面的依赖安装层）
COPY pygeomodels/ ./pygeomodels/
COPY pygeomodels_service.py .
COPY README.md .
COPY setup.py .
COPY setup.cfg .
COPY MANIFEST.in .

# 安装项目本身
RUN python setup.py bdist_wheel && \
    pip install dist/*.whl

# 暴露服务端口 (8050)
EXPOSE 8050

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://127.0.0.1:8050/mcp', timeout=5)" || exit 1

# 启动服务
CMD ["python", "pygeomodels_service.py"]
