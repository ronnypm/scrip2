# Imagen base con Python
FROM python:3.14-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar playwright dependencies (necesario para browsers)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (para cachear)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar playwright browsers
RUN playwright install chromium && \
    playwright install-deps

# Copiar código de la app
COPY . .

# Crear directorio output
RUN mkdir -p /app/output

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Puerto expuesto
EXPOSE 8080

# Comando para iniciar
CMD ["gunicorn", "server:app", "--workers", "1", "--bind", "0.0.0.0:8080"]
