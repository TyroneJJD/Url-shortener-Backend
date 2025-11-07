# URL Shortener - Backend

Backend minimalista para acortador de URLs con autenticación mediante cookies HTTP-only.

## 🚀 Stack

- **FastAPI** - Framework web async
- **PostgreSQL** - Base de datos
- **asyncpg** - Driver PostgreSQL async
- **JWT** - Autenticación con tokens
- **bcrypt** - Hash de contraseñas

## 📁 Estructura

```
Back-End/
├── config/              # Configuración (settings)
├── database/            # Conexión y esquema SQL
│   ├── connection.py
│   └── schema.sql
├── models/              # Modelos Pydantic (user, url, token)
├── services/            # Lógica de negocio (auth, url)
├── routes/              # Endpoints HTTP (auth, urls)
├── middleware/          # Autenticación con cookies
├── utils/               # Utilidades (security, url_generator)
├── documentacion/       # Documentación y pruebas
│   ├── TESTING.md
│   └── ARQUITECTURA.md
└── main.py              # Aplicación principal
```

## ⚡ Instalación Rápida

```bash
# Crear entorno virtual
python -m venv venv
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
copy .env.example .env
# Editar .env con tus credenciales

# Ejecutar aplicación
python main.py
```

**Servidor:** http://localhost:8000  
**Docs:** http://localhost:8000/docs

## 📡 Endpoints Principales

### Autenticación
- `POST /auth/register` - Registrar usuario
- `POST /auth/login` - Login (establece cookie HTTP-only)
- `POST /auth/refresh` - Refrescar token
- `POST /auth/logout` - Cerrar sesión
- `GET /auth/me` - Usuario actual

### URLs
- `GET /{short_code}` - Resolver y redirigir (301)
- `POST /urls` - Crear URL corta
- `GET /urls/me/all` - Listar mis URLs
- `PUT /urls/{url_id}` - Editar URL
- `DELETE /urls/{url_id}` - Eliminar URL

## 🔐 Seguridad

- Contraseñas hasheadas con **bcrypt**
- Tokens **JWT** firmados
- Cookies **HTTP-only** (no accesibles desde JavaScript)
- Cookies **secure** en producción (HTTPS)
- **SameSite=lax** para protección CSRF

## 🗄️ Base de Datos

### Tabla `users`
```sql
id, username, email, hashed_password, is_active, created_at, updated_at
```

### Tabla `urls`
```sql
id, short_code, original_url, user_id, clicks, is_active, is_private, 
created_at, updated_at, expires_at
```

**Características:**
- URLs públicas (accesibles sin autenticación)
- URLs privadas (requieren login)
- Códigos cortos de 7 caracteres (Base62: a-z, A-Z, 0-9)
- Soft delete (is_active)
- Contador de clicks

## 📊 Características

✅ Autenticación con cookies HTTP-only  
✅ URLs públicas y privadas  
✅ Códigos cortos autogenerados (7 chars)  
✅ ~3.5 trillones de combinaciones posibles  
✅ Contador de clicks  
✅ Soft delete  
✅ Sin migraciones - Esquema SQL simple  

## 🧪 Testing

Ver documentación completa en: [`documentacion/TESTING.md`](documentacion/TESTING.md)

## 🔧 Configuración

Variables de entorno requeridas en `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5433/database
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True
```

## 📝 Notas

- El frontend será React + Next.js
- NGINX actuará como reverse proxy (no se requiere CORS)
- Las tablas se crean automáticamente desde `database/schema.sql`
