# API Testing Guide

## 🌐 Base URL
```
http://localhost:8000
```

## 📋 Flujo Completo

### 1. Registrar Usuario
**POST** `/auth/register`
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "securepass123"
}
```

### 2. Login
**POST** `/auth/login`
```json
{
  "username": "testuser",
  "password": "securepass123"
}
```
✅ Establece cookie HTTP-only `access_token`

### 3. Validar Sesión (Me)
**GET** `/auth/me` 🔒

**Respuesta:** `200 OK`
```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "is_active": true,
    "created_at": "2025-11-08T12:00:00"
  }
}
```

**Ejemplo:**
```bash
# Validar sesión activa
curl -b cookies.txt http://localhost:8000/auth/me

# Si no hay cookie o expiró → 401 Unauthorized
```

**Nota:** Este endpoint usa sliding session, por lo que automáticamente renueva el token en cada llamada.

### 4. Crear URL Pública
**POST** `/urls` 🔒
```json
{
  "original_url": "https://www.google.com"
}
```
**Respuesta:**
```json
{
  "id": 1,
  "short_code": "aB3xR9K",
  "original_url": "https://www.google.com",
  "clicks": 0,
  "is_active": true,
  "is_private": false,
  "created_at": "2025-11-07T12:00:00"
}
```

### 5. Crear URL Privada
**POST** `/urls` 🔒
```json
{
  "original_url": "https://internal-docs.com",
  "is_private": true
}
```

### 6. Resolver URL
**GET** `/{short_code}`
- **Pública:** Acceso sin autenticación
- **Privada:** Requiere cookie 🔒

**Posibles respuestas:**

✅ **301 Redirect** → URL original (si todo OK)

🔄 **302 Redirect** → Frontend con parámetros de error:
- `http://localhost:3000/{short_code}?error=not_found` (URL no existe)
- `http://localhost:3000/{short_code}?error=unauthorized` (URL privada sin login)
  - **Bonus:** Establece cookie `redirect_after_login` con el `short_code` (5 min) para redirección post-login
- `http://localhost:3000/{short_code}?error=guest_forbidden` (URL privada, usuario guest intentando acceder)

**Ejemplo:**
```bash
# URL pública válida
curl -L http://localhost:8000/abc123
# → 301 a https://google.com

# URL no encontrada
curl -L http://localhost:8000/noexiste
# → 302 a http://localhost:3000/noexiste?error=not_found

# URL privada sin autenticación
curl -i http://localhost:8000/privado
# → 302 a http://localhost:3000/privado?error=unauthorized
# → Cookie: redirect_after_login=privado; HttpOnly; Max-Age=300

# URL privada con usuario guest
curl -i http://localhost:8000/privado -b guest_cookies.txt
# → 302 a http://localhost:3000/privado?error=guest_forbidden
```

### 7. Listar URLs
**GET** `/urls/me/all` 🔒

### 8. Editar URL
**PUT** `/urls/{url_id}` 🔒
```json
{
  "original_url": "https://new-url.com",
  "is_active": true,
  "is_private": false
}
```

### 8. Eliminar URL
**DELETE** `/urls/{url_id}` 🔒

### 9. Logout
**POST** `/auth/logout`

---

## 🧪 Testing con cURL

```bash
# 1. Registrar
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"pass123"}'

# 2. Login (guarda cookie)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"pass123"}' \
  -c cookies.txt

# 3. Validar sesión activa
curl http://localhost:8000/auth/me -b cookies.txt

# 4. Crear URL pública
curl -X POST http://localhost:8000/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://google.com"}' \
  -b cookies.txt

# 5. Crear URL privada
curl -X POST http://localhost:8000/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://internal.com","is_private":true}' \
  -b cookies.txt

# 6. Resolver URL pública (sin cookie)
curl -L http://localhost:8000/aB3xR9K

# 7. Resolver URL privada (con cookie)
curl -L http://localhost:8000/pR7vXtE -b cookies.txt

# 8. Ver mis URLs
curl http://localhost:8000/urls/me/all -b cookies.txt

# 9. Logout
curl -X POST http://localhost:8000/auth/logout -b cookies.txt
```

---

## 🔐 URLs Privadas vs Públicas

| Tipo | Autenticación | Acceso | Caso de Uso |
|------|---------------|--------|-------------|
| **Pública** | No requerida | Cualquiera | Marketing, redes sociales, compartir público |
| **Privada** | Requerida 🔒 | Solo usuarios autenticados | Documentos internos, recursos empresa |

---

## ✨ Generador de Códigos

- **Formato:** Base62 (a-z, A-Z, 0-9)
- **Longitud:** 7 caracteres
- **Combinaciones:** 62^7 ≈ 3.5 trillones
- **Verificación:** Unicidad automática
- **Escalable:** Incrementa longitud si necesario

**Ejemplos:**
- `aB3xR9K` (Pública)
- `Xy7Mn2Q` (Privada)
- `9kLpR4T` (Pública)

---

## 🌐 Swagger UI

Interfaz interactiva para probar todos los endpoints:

**URL:** http://localhost:8000/docs

**Pasos:**
1. Abrir Swagger UI
2. Registrar usuario en `/auth/register`
3. Login en `/auth/login`
4. Probar endpoints (cookie se establece automáticamente)
5. Crear URLs públicas y privadas
6. Probar redirecciones en el navegador

---

## 🔒 Leyenda

- 🔒 = Requiere Cookie de Autenticación
- Sin icono = Público (excepto URLs privadas en resolución)
