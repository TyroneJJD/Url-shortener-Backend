# 👥 Gestión de Usuarios

## 📋 Tipos de Usuarios

| Aspecto | Guest | Registered |
|---------|-------|------------|
| **URLs** | 5 máximo | ✅ Ilimitadas |
| **Expiración** | 7 días | ✅ Permanentes |
| **URLs privadas** | ❌ No | ✅ Sí |
| **Acceso privadas** | ❌ No | ✅ Sí |
| **Sesión** | 7 días | 30 min (auto-renueva) |
| **Migración** | ✅ A registered | - |

---

## 🔌 Endpoints Principales

### POST /auth/guest - Crear Sesión Guest
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```
Cookie establecida: 7 días (no renovable)

---

### POST /auth/register - Registrar Usuario
```json
{
  "username": "john",
  "email": "john@example.com",
  "password": "pass123"
}
```
Cookie establecida: 30 min (auto-renueva)

---

### POST /auth/login - Iniciar Sesión
```json
{
  "username": "john",
  "password": "pass123"
}
```

**Respuesta:**
```json
{
  "user": {
    "id": 1,
    "username": "john",
    "email": "john@example.com",
    "user_type": "registered"
  }
}
```

---

### POST /auth/migrate - Migrar Guest → Registered
```json
{
  "username": "john",
  "email": "john@example.com",
  "password": "pass123"
}
```

**Requiere:** Cookie de usuario guest  
**Resultado:** 
- Guest se convierte en registered
- URLs conservadas y ahora permanentes
- Cookie actualizada a 30 min (auto-renueva)

---

### GET /auth/me - Usuario Actual
Sin body. Retorna datos del usuario autenticado.

**Uso:** Recuperar sesión al cargar frontend.

---

### POST /auth/logout - Cerrar Sesión
Cookie eliminada (Max-Age=0).

---

## 🔄 Flujos de Usuario

### Flujo 1: Nuevo Usuario (Guest)
```
1. Frontend carga → Intenta GET /auth/me
2. No hay sesión → Genera UUID (crypto.randomUUID())
3. POST /auth/guest con UUID
4. Cookie establecida → Usuario puede crear 5 URLs
```

### Flujo 2: Registro Directo
```
1. Usuario llena formulario
2. POST /auth/register
3. Cookie establecida → Acceso completo
```

### Flujo 3: Guest → Registered
```
1. Guest alcanza límite (5 URLs)
2. Frontend muestra: "Regístrate para URLs ilimitadas"
3. POST /auth/migrate con datos de registro
4. URLs existentes ahora permanentes
5. Acceso completo
```

---

## 🔐 Seguridad

### Contraseñas
- **bcrypt** con 12 rondas (4096 iteraciones)
- Salt automático por cada password
- Mínimo 6 caracteres

### Cookies
```
HttpOnly: true      // No accesible desde JS (protección XSS)
Secure: true        // Solo HTTPS en producción
SameSite: lax       // Protección CSRF
Max-Age: 1800       // 30 min (registered)
```

### Sliding Session
```
Request t=0:   Token expira en t=30
Request t=10:  Token expira en t=40 (renovado)
Request t=25:  Token expira en t=55 (renovado)
Request t=60:  Token expirado → 401
```
Usuario activo = sesión nunca expira.

---

## 💻 Integración Frontend (React)

### Inicializar Autenticación
```javascript
async function initAuth() {
  try {
    const res = await fetch('/auth/me', {credentials: 'include'});
    if (res.ok) return await res.json();
  } catch {}
  
  // Crear guest
  let uuid = localStorage.getItem('guestUUID') || crypto.randomUUID();
  localStorage.setItem('guestUUID', uuid);
  
  const res = await fetch('/auth/guest', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({uuid}),
    credentials: 'include'
  });
  
  return await res.json();
}
```

### Registrar/Migrar
```javascript
async function register(formData, isGuest) {
  const endpoint = isGuest ? '/auth/migrate' : '/auth/register';
  
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(formData),
    credentials: 'include'
  });
  
  if (res.ok && isGuest) {
    localStorage.removeItem('guestUUID');
  }
  
  return await res.json();
}
```

### Login
```javascript
async function login(credentials) {
  const res = await fetch('/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(credentials),
    credentials: 'include'
  });
  
  return await res.json();
}
```

**Importante:** Siempre incluir `credentials: 'include'` para enviar/recibir cookies.

---

## 🎨 UI/UX Recomendado

### Banner para Guest
```jsx
{user.user_type === 'guest' && (
  <Alert>
    URLs usadas: {urlCount}/5
    <Button onClick={showRegisterModal}>
      Registrarse para ilimitadas
    </Button>
  </Alert>
)}
```

### Deshabilitar URLs Privadas para Guest
```jsx
<Checkbox
  checked={isPrivate}
  disabled={user.user_type === 'guest'}
>
  Privada {user.user_type === 'guest' && '(Solo registrados)'}
</Checkbox>
```

### Bloquear Creación al Límite
```jsx
<Button
  disabled={user.user_type === 'guest' && urlCount >= 5}
  onClick={createURL}
>
  Crear URL
</Button>
```

---

## 🔍 Troubleshooting

### "Not authenticated"
**Causa:** Cookie no enviada  
**Solución:** Agregar `credentials: 'include'` en fetch

### "Token expired" frecuente
**Causa:** Inactividad > 30 min  
**Solución:** Normal, pedir re-login

### Guest no puede migrar
**Causa:** Username/email ya existe  
**Solución:** Mostrar error específico del backend

### Cookie no persiste
**Causa:** Navegador en modo incógnito o configuración de cookies deshabilitada  
**Solución:** Pedir al usuario habilitar cookies

---

## 📚 Documentación Relacionada

- **[ARQUITECTURA.md](ARQUITECTURA.md)** - Arquitectura técnica del sistema
- **[README.md](../README.md)** - Inicio rápido
