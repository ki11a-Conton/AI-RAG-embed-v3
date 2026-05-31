FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 国内环境下载 HuggingFace 模型走镜像站，避免被墙
# 境外部署可删除此行或在 docker-compose.yml 中覆盖为空字符串
ENV HF_ENDPOINT=https://hf-mirror.com

EXPOSE 8501 8000

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
