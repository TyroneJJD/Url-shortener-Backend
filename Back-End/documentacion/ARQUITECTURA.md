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
    [Auto-Refresh Token] ← Sliding Session
          ↓
    [Actualizar Cookie]
          ↓
    [Ejecutar Endpoint]
          ↓
    Cliente ← Respuesta (con cookie actualizada)
```

**Sliding Session:** Mientras el usuario esté activo, la sesión se renueva automáticamente en cada request.
No es necesario llamar manualmente a `/refresh`.

**Endpoint de validación de sesión:**
- `GET /auth/me` - Devuelve datos del usuario autenticado y renueva la sesión automáticamente
- Útil para "recuperar" sesiones en el frontend al cargar la aplicación
- Si la cookie existe y es válida, retorna los datos del usuario

## 🔗 Flujo de Resolución URL

```
Cliente → GET /xyz123
          ↓
    [Buscar short_code en DB]
          ↓
    [¿URL existe?] ─No→ 302 Redirect → Frontend (/xyz123?error=not_found)
          ↓ Sí
    [¿is_private?] ─No→ [Incrementar clicks] → 301 Redirect → URL Original
          ↓ Sí
    [¿Usuario autenticado?] ─No→ [Set Cookie: redirect_after_login=xyz123]
          |                        ↓
          |                   302 Redirect → Frontend (/xyz123?error=unauthorized)
          ↓ Sí
    [¿Es usuario guest?] ─Sí→ 302 Redirect → Frontend (/xyz123?error=guest_forbidden)
          ↓ No (registered)
    [Incrementar clicks]
          ↓
    Cliente ← 301 Redirect → URL Original
```

**Nota:** En caso de error, el backend redirige al frontend para que maneje la UI de error.

**Flujo de redirección post-login:**
1. Usuario intenta acceder URL privada sin login → Cookie `redirect_after_login=xyz123` (5 min)
2. Frontend muestra formulario de login
3. Después de login exitoso, frontend lee la cookie y redirige a `/{short_code}`
4. Backend valida sesión y tipo de usuario (solo registered puede acceder URLs privadas)
5. Backend valida sesión y redirige a URL original

**Restricción de usuarios invitados:**
- Guests NO pueden acceder a URLs privadas, incluso si están autenticados
- Solo usuarios registered tienen acceso a URLs privadas
- Frontend debe mostrar mensaje: "Regístrate para acceder a URLs privadas"

El frontend puede mostrar:
- Página personalizada de "URL no encontrada"
- Formulario de login para URLs privadas con mensaje "Inicia sesión para ver este enlace"
- Mensaje especial para guests: "Esta URL es privada. Regístrate para acceder"

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
3. Genera JWT firmado con SECRET_KEY (30 min)
4. Establece cookie HTTP-only, secure, SameSite=lax

### Sliding Session (Auto-Refresh)
1. En cada request autenticado, el middleware genera un nuevo token
2. Actualiza la cookie automáticamente
3. **Resultado:** Mientras el usuario esté activo, la sesión nunca expira
4. Si está inactivo por 30+ minutos → 401, debe hacer login

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
