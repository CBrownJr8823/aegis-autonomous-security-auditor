FROM node:20-alpine AS web-builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY app ./app
COPY components ./components
COPY next.config.js postcss.config.js tailwind.config.ts tsconfig.json ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY backend ./backend
COPY --from=web-builder /app/.next /app/.next
COPY --from=web-builder /app/public /app/public
COPY --from=web-builder /app/node_modules /app/node_modules
COPY --from=web-builder /app/package.json /app/package.json
COPY --from=web-builder /app/next.config.js /app/next.config.js
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
