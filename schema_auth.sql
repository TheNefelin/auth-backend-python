-- ============================================================
-- Auth Unificado Transversal — Modelo de Tablas (PostgreSQL)
-- ============================================================
-- Soporte actual: email + contrasena (local) y Google (activo).
--   GitHub y Apple estan registrados pero INACTIVOS (is_active = FALSE)
--   para activarlos cuando se necesiten.
-- MFA/2FA: soporte TOTP + codigos de recuperacion.
-- Sin malas practicas:
--   * Sin columna auth_provider redundante en users.
--   * Sin ON DELETE CASCADE peligroso sobre usuarios.
--   * Sin merge automatico por email sin verificacion.
--   * Con CHECK constraints de integridad.
-- NOTA: client_id NO se guarda en BD. Viene de .env (variables de entorno).
--       La BD solo almacena: name, display_name, is_active (datos de negocio).
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------
-- Catalogo de roles de usuario
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_roles (
  id          SERIAL PRIMARY KEY,
  name        VARCHAR(50) UNIQUE NOT NULL,
  description VARCHAR(200),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- Catalogo de estados de usuario
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_status (
  id          SERIAL PRIMARY KEY,
  name        VARCHAR(50) UNIQUE NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- Catalogo de proveedores de autenticacion
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS auth_providers (
  id            SERIAL PRIMARY KEY,
  name          VARCHAR(50) UNIQUE NOT NULL,        -- 'local', 'google', 'github', 'apple'
  display_name  VARCHAR(100),
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- Usuarios (perfil principal, independiente del proveedor)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email          VARCHAR(255) UNIQUE,                       -- NULL permitido si es solo federado sin email propio
  password_hash  VARCHAR(255),                              -- NULL si es solo federado (google, github, etc.)
  name           VARCHAR(100),
  lastname       VARCHAR(100),
  picture_url    VARCHAR(1024),
  email_verified BOOLEAN NOT NULL DEFAULT FALSE,
  user_role_id   INT NOT NULL REFERENCES user_roles(id),
  status_id      INT NOT NULL REFERENCES user_status(id),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at     TIMESTAMPTZ,                               -- Soft delete: no se borran datos reales

  -- Integridad: el usuario debe poder autenticarse de al menos una forma
  CONSTRAINT chk_users_can_authenticate CHECK (
    password_hash IS NOT NULL OR email IS NOT NULL
  )
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at);

-- ------------------------------------------------------------
-- Identidades federadas (vinculo usuario <-> proveedor externo)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_identities (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  provider_id       INT NOT NULL REFERENCES auth_providers(id) ON DELETE RESTRICT,
  provider_user_id  VARCHAR(255) NOT NULL,                                          -- sub de Google, id de GitHub, Apple, etc.
  email             VARCHAR(255),                                                   -- email reportado por el proveedor
  profile_data      JSONB,                                                          -- datos crudos del perfil del proveedor
  is_primary        BOOLEAN NOT NULL DEFAULT FALSE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  UNIQUE(provider_id, provider_user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_identities_user ON user_identities(user_id);
CREATE INDEX IF NOT EXISTS idx_user_identities_provider ON user_identities(provider_id);
CREATE INDEX IF NOT EXISTS idx_user_identities_provider_user ON user_identities(provider_id, provider_user_id);
CREATE INDEX IF NOT EXISTS idx_user_identities_primary ON user_identities(user_id, is_primary) WHERE is_primary = TRUE;

-- Regla: solo una identidad primaria por usuario
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_identities_one_primary_per_user
ON user_identities(user_id) WHERE is_primary = TRUE;

-- ------------------------------------------------------------
-- Sesiones de usuario (refresh tokens)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_sessions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  refresh_token VARCHAR(512) UNIQUE NOT NULL,
  expires_at    TIMESTAMPTZ NOT NULL,
  is_revoked    BOOLEAN NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(refresh_token);

-- ------------------------------------------------------------
-- MFA / 2FA (TOTP + codigos de recuperacion)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_mfa (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  secret      VARCHAR(255) NOT NULL,     -- secreto TOTP (cifrado en reposo)
  is_enabled  BOOLEAN NOT NULL DEFAULT FALSE,
  enabled_at  TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_mfa_user ON user_mfa(user_id);

CREATE TABLE IF NOT EXISTS user_recovery_codes (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  code_hash   VARCHAR(255) NOT NULL,    -- hash del codigo (nunca en texto plano)
  used_at     TIMESTAMPTZ,              -- NULL si no se ha usado
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_recovery_codes_user ON user_recovery_codes(user_id);

-- ------------------------------------------------------------
-- Datos de semilla
-- ------------------------------------------------------------
INSERT INTO user_roles (name, description) VALUES
  ('admin', 'Administrador del sistema'),
  ('user',  'Usuario estandar')
ON CONFLICT (name) DO NOTHING;

INSERT INTO user_status (name) VALUES
  ('activo'),
  ('inactivo'),
  ('bloqueado')
ON CONFLICT (name) DO NOTHING;

-- Proveedores: local y Google activos. GitHub y Apple inactivos (is_active = FALSE)
-- NOTA: client_id y URLs de endpoints NO se guardan en BD. Vienen de .env.
--       La BD solo almacena: name, display_name, is_active (datos de negocio).
INSERT INTO auth_providers (name, display_name, is_active) VALUES
  ('local',  'Email + Contrasena', TRUE),
  ('google', 'Google', TRUE),
  ('github', 'GitHub', FALSE),
  ('apple',  'Apple ID', FALSE)
ON CONFLICT (name) DO NOTHING;
