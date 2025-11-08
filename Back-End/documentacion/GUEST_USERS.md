# Sistema de Usuarios Invitados (Guest Users)

## 📋 Descripción

Sistema de usuarios temporales que permite a visitantes usar el acortador de URLs sin registrarse, con limitaciones:

- **Límite:** 5 URLs por usuario invitado
- **Expiración:** URLs expiran en 7 días
- **Restricción:** Solo pueden crear URLs públicas (no privadas)
- **Acceso:** No pueden acceder/resolver URLs privadas (solo usuarios registrados)
- **Migración:** Pueden convertirse en usuarios registrados conservando sus URLs

---

## 🗄️ Cambios en Base de Datos

### Tabla `users`
```sql
- user_type: 'guest' | 'registered'
- guest_uuid: UUID único generado en frontend
- email: nullable (guests no tienen email)
- hashed_password: nullable (guests no tienen password)
```

### Tabla `urls`
```sql
- expires_at: TIMESTAMP nullable (solo para URLs de guests)
```

---

## 🔌 Endpoints

### 1. Crear Sesión de Invitado
**POST** `/auth/guest`

**Body:**
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Respuesta:** Cookie HTTP-only (7 días) + datos del usuario guest

---

### 2. Migrar a Usuario Registrado
**POST** `/auth/migrate`
- **Requiere:** Cookie de usuario guest

**Body:**
```json
{
  "username": "nuevo_username",
  "email": "usuario@example.com",
  "password": "password123"
}
```

**Resultado:**
- Convierte guest → registered
- Elimina `expires_at` de todas sus URLs (permanentes)
- Nueva cookie con token de 30 minutos

---

### 3. Crear URL (Modificado)
**POST** `/urls`
- **Guests:** Máximo 5 URLs, expiran en 7 días, **solo públicas** (is_private=false)
- **Registrados:** Ilimitadas, sin expiración, públicas o privadas

**Error si guest excede límite:**
```json
{
  "detail": "Guest users can only create 5 URLs. Please register for unlimited URLs."
}
```

**Error si guest intenta crear URL privada:**
```json
{
  "detail": "Guest users cannot create private URLs. Please register to use this feature."
}
```

---

### 4. Limpieza de URLs Expiradas (Admin)
**POST** `/admin/cleanup-expired-urls`
- **Requiere:** Header `X-Admin-Key` con `SECRET_KEY`

**Respuesta:**
```json
{
  "message": "Cleanup completed",
  "deleted_urls": 15
}
```

---

## 🔄 Flujo Frontend

### 1. Al Cargar Aplicación
```javascript
// Verificar si hay sesión activa
const response = await fetch('/auth/me');

if (!response.ok) {
  // No hay sesión, crear guest automáticamente
  const guestUUID = getOrCreateGuestUUID(); // localStorage
  
  await fetch('/auth/guest', {
    method: 'POST',
    body: JSON.stringify({ uuid: guestUUID })
  });
}
```

### 2. UI de Límite (Guest)
```javascript
{isGuest && (
  <Alert>
    Has creado {urlCount}/5 URLs. 
    <Button>Registrarse para URLs ilimitadas</Button>
  </Alert>
)}
```

### 3. Migración al Registrarse
```javascript
const handleRegister = async (formData) => {
  if (isGuest) {
    // Migración
    await fetch('/auth/migrate', {
      method: 'POST',
      body: JSON.stringify(formData)
    });
    
    clearGuestSession(); // Borrar UUID de localStorage
  } else {
    // Registro normal
    await fetch('/auth/register', { ... });
  }
};
```

---

## ⏰ Cron Job de Limpieza

### Configurar en servidor (Linux)
```bash
# Editar crontab
crontab -e

# Agregar job diario a las 3 AM
0 3 * * * /path/to/cleanup_cron.sh
```

### Script `cleanup_cron.sh`
```bash
#!/bin/bash
source .env
curl -X POST http://localhost:8000/admin/cleanup-expired-urls \
  -H "X-Admin-Key: $SECRET_KEY"
```

---

## 🔐 Seguridad

### Prevención de Abuso
1. **Rate Limiting por IP:** Máximo 3 sesiones guest por día (pendiente implementar)
2. **Validación en Backend:** Límite de 5 URLs verificado en servidor
3. **UUID Único:** Base de datos rechaza UUIDs duplicados
4. **URLs Públicas Solamente:** Guests no pueden crear URLs privadas (solo usuarios registrados)

### Limitaciones
- **UUID en localStorage:** Si el usuario borra datos, pierde acceso a sus URLs
- **Sin sincronización:** URLs guest no se comparten entre dispositivos
- **Sin URLs privadas:** Feature exclusivo para usuarios registrados
- **Solución:** Mostrar mensaje "Regístrate para acceso multiplataforma y URLs privadas"

---

## 📊 Métricas Útiles

### Consultas SQL
```sql
-- Contar usuarios guest activos
SELECT COUNT(*) FROM users WHERE user_type = 'guest';

-- URLs próximas a expirar (< 24h)
SELECT * FROM urls 
WHERE expires_at < NOW() + INTERVAL '24 hours' 
AND is_active = TRUE;

-- Tasa de migración guest → registered
SELECT 
  (SELECT COUNT(*) FROM users WHERE user_type = 'registered') * 100.0 /
  (SELECT COUNT(*) FROM users)
AS migration_rate;
```

---

## ✅ Testing

```bash
# 1. Crear sesión guest
curl -X POST http://localhost:8000/auth/guest \
  -H "Content-Type: application/json" \
  -d '{"uuid":"550e8400-e29b-41d4-a716-446655440000"}' \
  -c guest_cookies.txt

# 2. Crear 5 URLs (guest limit - todas públicas)
for i in {1..5}; do
  curl -X POST http://localhost:8000/urls \
    -H "Content-Type: application/json" \
    -d "{\"original_url\":\"https://example$i.com\",\"is_private\":false}" \
    -b guest_cookies.txt
done

# 3. Intento de crear URL privada (debe fallar)
curl -X POST http://localhost:8000/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://private.com","is_private":true}' \
  -b guest_cookies.txt
# → 403 Forbidden: "Guest users cannot create private URLs"

# 4. Intento de crear 6ta URL (debe fallar)
curl -X POST http://localhost:8000/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://example6.com"}' \
  -b guest_cookies.txt
# → 403 Forbidden

# 5. Migrar a usuario registrado
curl -X POST http://localhost:8000/auth/migrate \
  -H "Content-Type: application/json" \
  -d '{"username":"migrated_user","email":"test@test.com","password":"pass123"}' \
  -b guest_cookies.txt \
  -c registered_cookies.txt

# 6. Ahora como usuario registrado, crear URL privada (debe funcionar)
curl -X POST http://localhost:8000/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://private.com","is_private":true}' \
  -b registered_cookies.txt

# 7. Verificar que URLs no tienen expires_at
curl http://localhost:8000/urls/me/all -b registered_cookies.txt
```

---

## 🚀 Próximos Pasos

- [ ] Implementar rate limiting por IP
- [ ] Dashboard admin para ver estadísticas de guests
- [ ] Notificaciones de expiración (emails si migran)
- [ ] Telemetría: tracking de conversión guest → registered
