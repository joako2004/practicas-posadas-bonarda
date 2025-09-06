# practicas-posadas-bonarda

# 📋 Sistema de Logging - Posada

Documentación completa del sistema de logging para el proyecto **Sistema de Gestión Posada**.

## 📁 Ubicación del archivo

```
config/
└── logging_config.py    # Configuración principal del sistema de logging
```

## 🎯 Propósito

El sistema de logging proporciona un registro detallado y organizado de todas las actividades del sistema, facilitando:

- **Debugging** durante el desarrollo
- **Monitoreo** en producción  
- **Auditoría** de operaciones críticas
- **Resolución** de problemas

## 🏗️ Arquitectura del Sistema

### Estructura de Archivos de Log

```
logs/
├── app.log          # Logs generales de la aplicación
├── app.log.1        # Backup automático (cuando app.log > 10MB)
├── app.log.2        # Backup automático anterior
├── ...              # Hasta 5 backups
└── errors.log       # Solo errores críticos (ERROR y CRITICAL)
```

### Componentes Principales

| Componente | Descripción | Destino |
|------------|-------------|---------|
| **File Handler** | Logs completos con rotación automática | `logs/app.log` |
| **Console Handler** | Logs visibles en terminal (INFO+) | Terminal/Consola |
| **Error Handler** | Solo errores críticos | `logs/errors.log` |

## 📊 Niveles de Logging

| Nivel | Descripción | Cuándo usar | Visible en |
|-------|-------------|-------------|------------|
| `DEBUG` | Información muy detallada | Desarrollo y debugging | Solo archivos |
| `INFO` | Flujo normal de la aplicación | Operaciones importantes | Archivos + Consola |
| `WARNING` | Situaciones inesperadas no críticas | Advertencias | Archivos + Consola |
| `ERROR` | Errores que impiden operaciones | Fallos recuperables | Archivos + Consola + errors.log |
| `CRITICAL` | Errores que pueden colapsar el sistema | Fallos graves | Archivos + Consola + errors.log |

## 🚀 Instalación y Configuración

### 1. Importar el logger

```python
from config.logging_config import logger
```

### 2. Uso básico

```python
# Ejemplos de uso por nivel
logger.debug("Información de depuración detallada")
logger.info("Operación completada exitosamente") 
logger.warning("Advertencia: configuración por defecto")
logger.error("Error en conexión a base de datos")
logger.critical("Sistema fuera de servicio")
```

### 3. Logging en funciones

```python
def crear_cliente(nombre, email):
    logger.info(f"Creando cliente: {nombre}")
    try:
        # Lógica del negocio
        cliente = Cliente(nombre=nombre, email=email)
        logger.info(f"Cliente creado con ID: {cliente.id}")
        return cliente
    except Exception as e:
        logger.error(f"Error creando cliente {nombre}: {e}", exc_info=True)
        raise
```

## 📝 Formato de Logs

### Archivo (`app.log`)
```
2025-01-15 10:30:45 - INFO - Posada - crear_cliente:25 - Cliente creado con ID: 123
│              │       │      │         │          │     │
│              │       │      │         │          │     └─ Mensaje
│              │       │      │         │          └─ Línea de código
│              │       │      │         └─ Función donde se generó
│              │       │      └─ Nombre del logger
│              │       └─ Nivel del log
│              └─ Fecha y hora
└─ Timestamp completo
```

### Consola (simplificado)
```
10:30:45 - INFO - Cliente creado con ID: 123
```

## 🔧 Funciones Utilitarias

El sistema incluye funciones de conveniencia para casos comunes:

### `log_startup()`
```python
from config.logging_config import log_startup

log_startup()
# Output: 🚀 POSADA - Sistema iniciado
```

### `log_shutdown()`  
```python
from config.logging_config import log_shutdown

log_shutdown()
# Output: 🛑 POSADA - Sistema detenido
```

### `log_database_connection(success, details)`
```python
from config.logging_config import log_database_connection

# Conexión exitosa
log_database_connection(True, "PostgreSQL localhost:5432")
# Output: ✅ Conexión a base de datos exitosa PostgreSQL localhost:5432

# Conexión fallida
log_database_connection(False, "Timeout después de 30s")
# Output: ❌ Error en conexión a base de datos Timeout después de 30s
```

### `log_api_request(method, endpoint, status_code)`
```python
from config.logging_config import log_api_request

log_api_request("GET", "/api/clientes", 200)
# Output: 🌐 GET /api/clientes - Status: 200
```

## ⚙️ Configuración Avanzada

### Rotación de Archivos

El sistema usa **RotatingFileHandler** con la siguiente configuración:

```python
- Tamaño máximo por archivo: 10MB
- Número de backups: 5 archivos
- Encoding: UTF-8
```

**Comportamiento:**
1. `app.log` crece hasta 10MB
2. Se renombra a `app.log.1`
3. Se crea nuevo `app.log` vacío
4. Los backups más antiguos se eliminan automáticamente

### Personalización de Niveles

Para cambiar el nivel mínimo en consola:

```python
console_handler.setLevel(logging.WARNING)  # Solo WARNING, ERROR, CRITICAL
```

Para cambiar el nivel mínimo en archivos:

```python
file_handler.setLevel(logging.INFO)  # Solo INFO y superiores
```

## 📊 Mejores Prácticas

### ✅ Hacer

```python
# Usar f-strings para mensajes dinámicos
logger.info(f"Usuario {user_id} realizó acción: {action}")

# Incluir exc_info=True para errores con stack trace
try:
    operacion_riesgosa()
except Exception as e:
    logger.error(f"Error en operación: {e}", exc_info=True)

# Ser específico en los mensajes
logger.info("Cliente creado exitosamente con ID: 123")
```

### ❌ Evitar

```python
# No usar concatenación de strings
logger.info("Usuario " + str(user_id) + " hizo algo")

# No loggear información sensible
logger.info(f"Password del usuario: {password}")  # ¡NUNCA!

# No usar solo "Error" como mensaje
logger.error("Error")  # Poco informativo
```

## 🔍 Monitoreo y Debugging

### Encontrar errores rápidamente

```bash
# Ver solo errores del día actual
grep "$(date +%Y-%m-%d)" logs/errors.log

# Ver últimos 50 errores
tail -n 50 logs/errors.log

# Monitorear logs en tiempo real
tail -f logs/app.log
```

### Análisis de logs

```bash
# Contar tipos de logs del día
grep "$(date +%Y-%m-%d)" logs/app.log | cut -d'-' -f3 | sort | uniq -c

# Buscar logs de una función específica
grep "crear_cliente" logs/app.log
```

## 🚨 Solución de Problemas

### Problema: No se crean archivos de log

**Causa:** Permisos de escritura insuficientes
```bash
# Verificar permisos
ls -la logs/

# Dar permisos de escritura
chmod 755 logs/
```

### Problema: Logs duplicados

**Causa:** Múltiples inicializaciones del logger
```python
# Solución: Verificar que solo se importe una vez
logger.handlers.clear()  # Limpia handlers duplicados
```

### Problema: Archivos de log muy grandes

**Causa:** Rotación no funcionando
```python
# Verificar configuración de RotatingFileHandler
maxBytes=10 * 1024 * 1024  # 10MB
backupCount=5
```

## 📈 Métricas y Estadísticas

Para generar estadísticas de uso:

```python
# Contar logs por nivel
import re
from collections import Counter

def analizar_logs():
    with open('logs/app.log', 'r') as f:
        logs = f.readlines()
    
    niveles = []
    for line in logs:
        match = re.search(r' - (DEBUG|INFO|WARNING|ERROR|CRITICAL) - ', line)
        if match:
            niveles.append(match.group(1))
    
    return Counter(niveles)

# Resultado: {'INFO': 1250, 'ERROR': 45, 'WARNING': 12, ...}
```

## 🔄 Mantenimiento

### Limpieza automática (opcional)

Para limpiar logs antiguos automáticamente:

```python
import os
import time
from pathlib import Path

def limpiar_logs_antiguos(dias=30):
    """Elimina logs más antiguos que X días"""
    logs_dir = Path('logs')
    limite = time.time() - (dias * 24 * 60 * 60)
    
    for archivo in logs_dir.glob('*.log.*'):
        if archivo.stat().st_mtime < limite:
            archivo.unlink()
            logger.info(f"Log antiguo eliminado: {archivo}")
```

## 📞 Soporte

Para problemas con el sistema de logging:

1. Verificar que la carpeta `logs/` tenga permisos de escritura
2. Revisar que no haya imports circulares
3. Confirmar que solo se inicializa el logger una vez
4. Consultar los logs de error en `logs/errors.log`

---

**Versión:** 1.0  
**Proyecto:** Sistema de Gestión Posada
**Última actualización:** Enero 2025  