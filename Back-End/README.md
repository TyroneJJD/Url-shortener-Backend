# URL Shortener - Backend

Backend HTTP simple y mínimo para un acortador de URLs con autenticación mediante cookies HTTP-only.

## 🚀 Características

- **Autenticación con cookies HTTP-only**: Seguro y sin necesidad de manejar tokens en el frontend
- **PostgreSQL**: Base de datos única sin migraciones complejas
- **FastAPI**: Framework moderno y rápido
- **Arquitectura limpia**: Separación de componentes (models, services, routes, utils)
- **Sin boilerplate innecesario**: Código mínimo y directo

## 📁 Estructura del Proyecto

```
Back-End/
├── config/              # Configuración de la aplicación
│   ├── __init__.py
│   └── settings.py      # Settings con Pydantic
├── database/            # Gestión de base de datos
│   ├── __init__.py
│   └── connection.py    # Pool de conexiones y setup
├── models/              # Modelos Pydantic
│   ├── __init__.py
│   ├── user.py
│   ├── url.py
│   └── token.py
├── services/            # Lógica de negocio
│   ├── __init__.py
│   ├── auth_service.py
│   └── url_service.py
├── routes/              # Endpoints de la API
│   ├── __init__.py
│   ├── auth.py
│   └── urls.py
├── middleware/          # Middleware de autenticación
│   ├── __init__.py
│   └── auth.py
├── utils/               # Utilidades
│   ├── __init__.py
│   ├── security.py      # JWT y hashing
│   └── url_generator.py # Generador de códigos
├── main.py              # Aplicación principal
├── requirements.txt     # Dependencias
├── .env.example         # Ejemplo de variables de entorno
└── README.md
```

## 🔧 Instalación

1. **Clonar el repositorio y navegar a la carpeta**

2. **Crear entorno virtual**
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows PowerShell
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Configurar PostgreSQL**
```sql
CREATE DATABASE urlshortener;
```

6. **Ejecutar la aplicación**
```bash
python main.py
```

La aplicación estará disponible en `http://localhost:8000`

## 📡 Endpoints

### Autenticación

#### `POST /auth/register`
Registrar un nuevo usuario (público)
```json
{
  "username": "usuario",
  "email": "email@example.com",
  "password": "password123"
}
```

#### `POST /auth/login`
Login (público, establece cookie HTTP-only)
```json
{
  "username": "usuario",
  "password": "password123"
}
```

#### `POST /auth/refresh`
Refrescar token (requiere cookie)

#### `POST /auth/logout`
Logout (elimina cookie)

#### `GET /auth/me`
Obtener información del usuario actual (requiere cookie)

### URLs

#### `GET /{short_code}`
Resolver URL corta y redirigir (público)
- Retorna: 301 Redirect a la URL original

#### `POST /urls`
Crear URL corta (requiere cookie auth)
```json
{
  "original_url": "https://example.com/very/long/url",
  "custom_short_code": "mi-url",  // Opcional
  "expires_at": "2024-12-31T23:59:59"  // Opcional
}
```

#### `GET /urls/me/all`
Obtener todas las URLs del usuario actual (requiere cookie auth)

#### `PUT /urls/{url_id}`
Editar URL (requiere cookie auth)
```json
{
  "original_url": "https://new-url.com",  // Opcional
  "is_active": true,  // Opcional
  "expires_at": "2024-12-31T23:59:59"  // Opcional
}
```

#### `DELETE /urls/{url_id}`
Eliminar URL (soft delete, requiere cookie auth)

## 🗄️ Base de Datos

### Tabla `users`
- `id`: Serial Primary Key
- `username`: Varchar(50) Unique
- `email`: Varchar(100) Unique
- `hashed_password`: Varchar(255)
- `is_active`: Boolean
- `created_at`: Timestamp
- `updated_at`: Timestamp

### Tabla `urls`
- `id`: Serial Primary Key
- `short_code`: Varchar(20) Unique
- `original_url`: Text
- `user_id`: Integer (FK -> users.id)
- `clicks`: Integer
- `is_active`: Boolean
- `created_at`: Timestamp
- `updated_at`: Timestamp
- `expires_at`: Timestamp (nullable)

## 🔐 Seguridad

- Contraseñas hasheadas con bcrypt
- Tokens JWT firmados
- Cookies HTTP-only (no accesibles desde JavaScript)
- Cookies secure en producción (HTTPS)
- SameSite=lax para protección CSRF

## 🛠️ Desarrollo

### Ejecutar en modo desarrollo
```bash
python main.py
# O con uvicorn directamente:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Ver documentación interactiva
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📝 Notas

- No se requiere configuración de CORS ya que NGINX actuará como proxy
- Las tablas se crean automáticamente al iniciar la aplicación (no hay migraciones)
- El frontend será desarrollado en React + Next.js
- Los códigos cortos se generan aleatoriamente (6 caracteres por defecto)
- Los usuarios pueden crear códigos personalizados

## 🚧 Próximas Funcionalidades

- Estadísticas de clicks
- Análisis de geolocalización
- Rate limiting
- Cache con Redis
- Exportación de datos
