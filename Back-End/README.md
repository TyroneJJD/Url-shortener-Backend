# 🔗 URL Shortener - Backend

Backend para acortador de URLs con autenticación, usuarios invitados/registrados, URLs privadas y paginación.

## ⚡ Inicio Rápido

1. **Requisitos:** Python 3.10+, PostgreSQL 12+, pip
2. **Instalación:**
   ```bash
   git clone <repository-url>
   cd Back-End
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
3. **Configurar `.env`:**
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/database
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   DEBUG=True
   FRONTEND_URL=http://localhost:3000
   ```
4. **Base de datos:**
    Desde la carpeta raiz del repositorio
   ```bash
      cd Docker
      docker-compose up
   ```
5. **Ejecutar:**
   ```bash
   python main.py
   ```

## 📚 Documentación

- [ARQUITECTURA.md](documentacion/ARQUITECTURA.md) - Diseño y stack
- [USUARIOS.md](documentacion/USUARIOS.md) - Flujos y endpoints de usuarios

---

