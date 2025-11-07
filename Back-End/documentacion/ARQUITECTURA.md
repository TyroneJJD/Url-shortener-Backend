# Arquitectura del Sistema

## 📐 Diseño

El backend sigue una arquitectura en capas limpia y separada:

```
┌─────────────────┐
│     Routes      │  ← HTTP Endpoints
├─────────────────┤
│   Middleware    │  ← Autenticación
├─────────────────┤
│    Services     │  ← Lógica de Negocio
├─────────────────┤
│     Models      │  ← Validación Pydantic
├─────────────────┤
│    Database     │  ← PostgreSQL Pool
└─────────────────┘
```

## 🔄 Flujo de Autenticación

```
Cliente → POST /auth/login
          ↓
    [Validar Credenciales]
          ↓
    [Generar JWT Token]
          ↓
    [Establecer Cookie HTTP-only]
          ↓
    Cliente ← Cookie establecida

Cliente → GET /urls/me/all (con cookie)
          ↓
    [Middleware: Verificar Cookie]
          ↓
    [Decodificar JWT]
          ↓
    [Obtener Usuario de DB]
          ↓
    [Ejecutar Endpoint]
          ↓
    Cliente ← Respuesta
```

## 🔗 Flujo de Resolución URL

```
Cliente → GET /xyz123
          ↓
    [Buscar short_code en DB]
          ↓
    [¿URL existe?] ─No→ 404 Not Found
          ↓ Sí
    [¿is_private?] ─No→ [Incrementar clicks] → 301 Redirect
          ↓ Sí
    [¿Usuario autenticado?] ─No→ 401 Unauthorized
          ↓ Sí
    [Incrementar clicks]
          ↓
    Cliente ← 301 Redirect
```

## 🗂️ Estructura de Módulos

### `/config`
- **Propósito:** Configuración centralizada
- **Contenido:** Settings de Pydantic con variables de entorno

### `/database`
- **Propósito:** Gestión de base de datos
- **Contenido:** Pool de conexiones asyncpg, schema SQL

### `/models`
- **Propósito:** Modelos de datos
- **Contenido:** Schemas Pydantic para validación y serialización

### `/services`
- **Propósito:** Lógica de negocio
- **Contenido:** Operaciones CRUD, reglas de negocio

### `/routes`
- **Propósito:** Endpoints HTTP
- **Contenido:** Definición de rutas FastAPI

### `/middleware`
- **Propósito:** Interceptores de peticiones
- **Contenido:** Autenticación, validación de cookies

### `/utils`
- **Propósito:** Funciones auxiliares
- **Contenido:** Seguridad (JWT, bcrypt), generador de códigos

## 🔐 Seguridad

### Autenticación
1. Usuario envía credenciales
2. Backend verifica con bcrypt
3. Genera JWT firmado con SECRET_KEY
4. Establece cookie HTTP-only, secure, SameSite=lax

### Autorización
1. Middleware extrae cookie de request
2. Decodifica y valida JWT
3. Obtiene usuario de DB
4. Inyecta usuario en endpoint via Depends()

### Protección
- **Cookies HTTP-only:** No accesibles desde JavaScript
- **Secure flag:** Solo HTTPS en producción
- **SameSite:** Protección CSRF
- **JWT firmado:** Integridad del token
- **bcrypt:** Hash de contraseñas con salt

## 📊 Base de Datos

### Relaciones
```
users (1) ──→ (N) urls
```

### Índices
- `urls.short_code` (UNIQUE, WHERE is_active = TRUE)

### Estrategia
- **Soft Delete:** `is_active = FALSE` en lugar de DELETE
- **Timestamps:** Automáticos con triggers
- **Pool de Conexiones:** asyncpg para alto rendimiento
