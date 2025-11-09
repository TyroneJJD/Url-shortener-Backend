# 🏗️ Arquitectura del Sistema


## 📐 Patrón de Diseño: Arquitectura en Capas

El backend implementa una **Arquitectura en Capas** con separación clara de responsabilidades:

- **Routes:** Endpoints HTTP (FastAPI)
- **Middleware:** Autenticación JWT
- **Services:** Lógica de negocio
- **Models:** Validación (Pydantic)
- **Database:** PostgreSQL + asyncpg

## 🔧 Stack

| Componente      | Tecnología         |
|-----------------|-------------------|
| Framework       | FastAPI           |
| Base de Datos   | PostgreSQL        |
| Driver BD       | asyncpg           |
| Autenticación   | JWT + bcrypt      |
| Validación      | Pydantic          |

## 🗄️ Esquema BD

**users**: id, username, email, hashed_password, user_type, guest_uuid, is_active, created_at

**urls**: id, short_code, original_url, user_id, clicks, is_active, is_private, created_at, expires_at

**url_access_history**: id, url_id, user_email, user_type, accessed_at

## 🔐 Autenticación

- JWT en cookies HTTP-only (protege contra XSS)
- Sliding session: token renovado en cada request
- Guest: 5 URLs, 7 días | Registered: ilimitado

## 🛡️ Seguridad

- Contraseñas: bcrypt
- SQL Injection: asyncpg (prepared statements)
- CORS: solo frontend permitido

## 🔄 Features Clave

- Paginación: `GET /urls/me/all?offset=0&limit=20`
- Historial de accesos: `GET /urls/me/all?with_history=true`
- Exportar JSON: `GET /urls/me/all?export=true`
- Carga masiva: `POST /urls/bulk` (máx 100 URLs)

## 📂 Estructura Carpetas

```
Back-End/
├── config/         # Settings (Pydantic)
├── database/       # Pool + schema
├── models/         # Validación
├── middleware/     # Auth JWT
├── services/       # Lógica negocio
├── routes/         # Endpoints HTTP
├── utils/          # Seguridad, generador
├── documentacion/  # Docs
└── main.py         # Entry point
```

## 📈 Performance

- Pool de conexiones asyncpg
- Stack 100% async/await
- Índices clave: short_code, user_id, url_id

## 📚 Documentación

- [`USUARIOS.md`](USUARIOS.md) - Usuarios y endpoints
- [`README.md`](../README.md) - Inicio rápido



