FROM python:3.11

# 安装 Node.js （满足 >=18）及必要工具
RUN apt-get update \
  && apt-get install -y --no-install-recommends nodejs npm curl \
  && rm -rf /var/lib/apt/lists/*

# 从 uv 官方镜像复制 uv
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# 先复制依赖描述文件以利用缓存
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY backend/pyproject.toml backend/uv.lock ./backend/

# 安装依赖（Node + Python）
RUN npm ci \
  && npm ci --prefix frontend \
  && cd backend && uv sync --frozen

# 复制项目源码
COPY . .

# 构建前端生产产物（输出到 frontend/dist）
RUN npm run build

# 生产环境默认关闭 DEBUG（如需可在运行时覆盖）
ENV FLASK_DEBUG=false

EXPOSE 3000 5001

# 健康检查：探测后端 /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://localhost:5001/health || exit 1

# 以生产模式启动：后端用 waitress(WSGI)，前端用 vite preview 提供静态构建产物
CMD ["npm", "run", "start"]
