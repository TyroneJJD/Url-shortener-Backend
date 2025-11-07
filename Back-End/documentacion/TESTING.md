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

### 3. Crear URL Pública
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

### 4. Crear URL Privada
**POST** `/urls` 🔒
```json
{
  "original_url": "https://internal-docs.com",
  "is_private": true
}
```

### 5. Resolver URL
**GET** `/{short_code}`
- **Pública:** Acceso sin autenticación
- **Privada:** Requiere cookie 🔒

Retorna: `301 Redirect` a URL original

### 6. Listar URLs
**GET** `/urls/me/all` 🔒

### 7. Editar URL
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

### 9. Refrescar Token
**POST** `/auth/refresh` 🔒

### 10. Logout
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

# 3. Crear URL pública
curl -X POST http://localhost:8000/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://google.com"}' \
  -b cookies.txt

# 4. Crear URL privada
curl -X POST http://localhost:8000/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://internal.com","is_private":true}' \
  -b cookies.txt

# 5. Resolver URL pública (sin cookie)
curl -L http://localhost:8000/aB3xR9K

# 6. Resolver URL privada (con cookie)
curl -L http://localhost:8000/pR7vXtE -b cookies.txt

# 7. Ver mis URLs
curl http://localhost:8000/urls/me/all -b cookies.txt
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
