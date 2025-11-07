# Pruebas del API - URL Shortener

## Base URL
```
http://localhost:8000
```

---

## 🔐 Autenticación

### 1. Registrar Usuario
**POST** `/auth/register`

```json
{
  "username": "usuario_test",
  "email": "test@example.com",
  "password": "password123"
}
```

### 2. Login (Establece Cookie)
**POST** `/auth/login`

```json
{
  "username": "usuario_test",
  "password": "password123"
}
```
✅ **Respuesta:** Cookie HTTP-only `access_token` se establece automáticamente

### 3. Obtener Usuario Actual
**GET** `/auth/me`

🔒 Requiere Cookie

### 4. Refrescar Token
**POST** `/auth/refresh`

🔒 Requiere Cookie

### 5. Logout
**POST** `/auth/logout`

---

## 🔗 URLs

### 6. Crear URL Corta (Autogenerada)
**POST** `/urls`

🔒 Requiere Cookie

```json
{
  "original_url": "https://www.google.com/search?q=very+long+url+example"
}
```

✅ **Respuesta:**
```json
{
  "id": 1,
  "short_code": "aB3xR9K",
  "original_url": "https://www.google.com/search?q=very+long+url+example",
  "clicks": 0,
  "is_active": true,
  "created_at": "2025-11-07T12:00:00"
}
```

**Nota:** El `short_code` se genera automáticamente usando 7 caracteres alfanuméricos (a-z, A-Z, 0-9).
Esto proporciona ~3.5 trillones de combinaciones posibles.

### 7. Resolver URL (Redirección 301)
**GET** `/{short_code}`

🌐 **Público** - No requiere autenticación

Ejemplo: `GET /aB3xR9K`

✅ Retorna: **301 Redirect** a la URL original
✅ Incrementa el contador de clicks

### 8. Listar Mis URLs
**GET** `/urls/me/all`

🔒 Requiere Cookie

### 9. Editar URL
**PUT** `/urls/{url_id}`

🔒 Requiere Cookie

```json
{
  "original_url": "https://nueva-url.com",
  "is_active": true
}
```

Nota: Solo puedes editar tus propias URLs

### 10. Eliminar URL (Soft Delete)
**DELETE** `/urls/{url_id}`

🔒 Requiere Cookie

---

## 📊 Health Check

### 11. Verificar Estado del API
**GET** `/health`

🌐 Público

```json
{
  "status": "healthy"
}
```

---

## 🧪 Prueba Rápida con cURL

### Registrar y Login
```bash
# 1. Registrar usuario
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"pass123"}'

# 2. Login (guarda la cookie)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"pass123"}' \
  -c cookies.txt

# 3. Crear URL corta (usa la cookie)
curl -X POST http://localhost:8000/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://google.com"}' \
  -b cookies.txt

# 4. Resolver URL (en el navegador o con curl)
curl -L http://localhost:8000/aB3xR9K

# 5. Ver mis URLs
curl http://localhost:8000/urls/me/all -b cookies.txt
```

---

## 🌐 Prueba en el Navegador

1. **Abrir Swagger UI:** http://localhost:8000/docs
2. **Registrar usuario** en `/auth/register`
3. **Login** en `/auth/login` (la cookie se establece automáticamente)
4. **Crear URL** en `/urls`
5. **Probar redirección** abriendo: `http://localhost:8000/{short_code}`

---

## ✨ Características del Generador de Códigos

### Sistema de Generación Automática:
- **Longitud:** 7 caracteres por defecto
- **Caracteres:** a-z, A-Z, 0-9 (Base62)
- **Combinaciones:** 62^7 = ~3.5 trillones posibles
- **Unicidad:** Verificación automática en base de datos
- **Escalable:** Incrementa longitud automáticamente si es necesario

### Ejemplos de URLs generadas:
```
http://localhost:8000/aB3xR9K
http://localhost:8000/Xy7Mn2Q
http://localhost:8000/9kLpR4T
```

**Ventajas:**
- Corto y fácil de compartir
- Sin colisiones (verifica unicidad)
- Distribuido aleatoriamente
- Profesional y limpio
