# FungiCloud ☁️

**Servidor en la nube para gestión de usuarios, facturación y sincronización del ecosistema FungiControl**

## 🏗️ Arquitectura

FungiCloud implementa el modelo **Hub Local + Cloud Management**:

```
┌─────────────────────────────────────────────────────────────┐
│                       FUNGICLOUD (Cloud)                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Users    │  │  Billing   │  │   Admin    │            │
│  │   Auth     │  │  Stripe    │  │  Dashboard │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│  ┌────────────────────────────────────────────┐             │
│  │       PostgreSQL Database                  │             │
│  │  - users, billing, local_servers           │             │
│  │  - sync_data, sync_events                  │             │
│  └────────────────────────────────────────────┘             │
└──────────────────────▲───────────────────────────────────────┘
                       │ HTTPS Sync cada 15 min
                       │
      ┌────────────────┴────────────────┐
      │                                  │
┌─────▼────────┐                 ┌──────▼───────┐
│ raspServer   │                 │ raspServer   │
│ (User A LAN) │                 │ (User B LAN) │
│  - SQLite    │                 │  - SQLite    │
│  - MQTT      │                 │  - MQTT      │
│  - Sensors   │                 │  - Sensors   │
└──────────────┘                 └──────────────┘
```

### Responsabilidades

**FungiCloud (Cloud)**:
- Gestión de usuarios y autenticación (JWT)
- Facturación con Stripe (planes free/starter/advance/expert)
- Sincronización de datos desde servidores locales
- Dashboard de administración
- Sistema de alertas (servidores offline, etc.)
- Almacenamiento centralizado de métricas agregadas

**raspServerNative (Local)**:
- Control en tiempo real de sensores y actuadores vía MQTT
- Base de datos SQLite local con toda la información
- Operación offline (no depende de internet)
- Sincronización periódica con FungiCloud
- Autonomía total del cultivo

## 📋 Funcionalidades

### ✅ Implementadas

1. **Autenticación**
   - Registro de usuarios
   - Login con JWT
   - Verificación de tokens
   - Roles (user, admin)

2. **Facturación**
   - 4 planes: Free, Starter ($5), Advance ($17.50), Expert ($29.50)
   - Integración con Stripe Checkout
   - Gestión de suscripciones
   - Webhooks de Stripe

3. **Sincronización**
   - Registro de servidores locales
   - Recepción de datos agregados (sensor data, eventos)
   - Tracking de estado online/offline
   - Historial de sincronizaciones

4. **Admin Dashboard**
   - Vista general del sistema (users, revenue, servers)
   - Gestión de usuarios
   - Monitoreo de servidores
   - Métricas en tiempo real

5. **Sistema de Alertas**
   - Monitoreo de servidores offline (>15 min sin sync)
   - Emails automáticos a usuarios
   - Configuración por servidor (habilitar/deshabilitar alertas)
   - Email alternativo para alertas

## 🚀 Instalación

### Requisitos

- Python 3.9+
- PostgreSQL 12+
- Cuenta de Stripe
- (Opcional) SMTP para alertas por email

### 1. Clonar y configurar entorno

```bash
cd fungicloud
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar PostgreSQL

```sql
CREATE DATABASE fungicloud;
CREATE USER fungicloud_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE fungicloud TO fungicloud_user;
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

Variables importantes:
- `DATABASE_URL`: Conexión a PostgreSQL
- `SECRET_KEY`: Secreto de Flask (generar uno aleatorio)
- `JWT_SECRET_KEY`: Secreto para JWT (generar uno aleatorio)
- `STRIPE_SECRET_KEY`: API key de Stripe
- `SMTP_USER` y `SMTP_PASSWORD`: Para alertas por email

### 4. Inicializar base de datos

```bash
python -c "from database import init_database; init_database()"
```

### 5. Ejecutar

```bash
# Desarrollo
python app.py

# Producción con gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📡 API Endpoints

### Autenticación

- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Login (devuelve JWT)
- `GET /api/auth/verify` - Verificar token

### Facturación

- `GET /api/billing/status` - Estado de facturación del usuario
- `GET /api/billing/plans` - Listar planes disponibles
- `POST /api/billing/checkout/create` - Crear sesión de Stripe Checkout
- `POST /api/billing/webhooks/stripe` - Webhooks de Stripe

### Sincronización (para raspServerNative)

- `POST /api/sync/register` - Registrar servidor local
- `POST /api/sync/data` - Enviar datos sincronizados
- `GET /api/sync/servers` - Listar servidores del usuario

### Admin (requiere is_admin=True)

- `GET /api/admin/dashboard` - Dashboard completo
- `GET /api/admin/users` - Listar todos los usuarios
- `GET /api/admin/users/<id>` - Detalles de un usuario
- `POST /api/admin/users/<id>/suspend` - Suspender usuario
- `GET /api/admin/servers` - Listar todos los servidores

### Alertas

- `GET /api/alerts/servers/offline` - Servidores offline del usuario
- `PUT /api/alerts/servers/<id>/settings` - Configurar alertas

## 🔐 Autenticación

Todos los endpoints (excepto `/auth/register` y `/auth/login`) requieren JWT:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 💰 Planes de Facturación

| Plan     | Precio/mes | Cultivos | Histórico | Reportes | Alertas |
|----------|------------|----------|-----------|----------|---------|
| Free     | $0         | 1        | 7 días    | ❌       | ❌      |
| Starter  | $5         | 3        | 30 días   | ✅       | ✅      |
| Advance  | $17.50     | 10       | 90 días   | ✅       | ✅      |
| Expert   | $29.50     | ∞        | 365 días  | ✅       | ✅      |

## 🔧 Configuración de Producción

### DigitalOcean Droplet (Recomendado)

1. Crear droplet Ubuntu 22.04 ($12/mo)
2. Instalar PostgreSQL
3. Configurar Nginx como proxy reverso
4. SSL con Let's Encrypt
5. Gunicorn con systemd service

### Variables de entorno críticas

```bash
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@localhost/fungicloud
SECRET_KEY=<generar-secreto-aleatorio-fuerte>
JWT_SECRET_KEY=<generar-secreto-aleatorio-fuerte>
```

## 🧪 Testing

```bash
# Ejecutar tests (cuando se implementen)
pytest tests/

# Test de conexión a DB
python -c "from database import get_engine; print(get_engine().url)"
```

## 📊 Monitoreo

El sistema incluye:
- Health check en `/health`
- Monitor de alertas (background thread)
- Logs en stdout/stderr
- Métricas en dashboard de admin

## 🚨 Sistema de Alertas

El monitor de alertas ejecuta cada 5 minutos (configurable con `ALERT_CHECK_INTERVAL`):

1. Busca servidores con `last_seen` > 15 min
2. Actualiza estado a `offline`
3. Envía email al usuario
4. Registra en logs

Configurar SMTP en `.env` para habilitar emails.

## 🤝 Integración con raspServerNative

El servidor local debe sincronizar cada 15 minutos:

```python
# En raspServerNative
import requests

def sync_to_cloud():
    data = {
        "server_id": "unique-server-id",
        "avg_temperature": 25.5,
        "avg_humidity": 80.0,
        # ... más datos
    }
    headers = {"Authorization": f"Bearer {user_jwt_token}"}
    response = requests.post(
        "https://fungicloud.com/api/sync/data",
        json=data,
        headers=headers
    )
```

## 📝 TODO

- [ ] Tests unitarios y de integración
- [ ] Documentación completa de API (Swagger)
- [ ] Rate limiting
- [ ] Cache con Redis
- [ ] Métricas con Prometheus
- [ ] Logs estructurados
- [ ] Backup automático de PostgreSQL

## 📄 Licencia

Proyecto de grado - FungiControl

---

**Desarrollado con ❤️ para el ecosistema FungiControl**
