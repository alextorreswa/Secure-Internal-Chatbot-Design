/*
===========================================================
  DATABASE: chatbot_system
  PURPOSE:  Secure, on-premise chatbot system for Cascade Freight Systems
  OWNER:    postgres (or your custom role)
  CREATED:  2025-11-11
  VERSION:  Initial schema (v1.0)

  DESCRIPTION:
    This database supports a secure, auditable chatbot system
    with role-based access, chat logging, anomaly reporting,
    and document reference tracking. Designed for modular
    expansion and integration with internal admin tools.

  MODULES:
    - users: Authenticated user accounts with MFA support
    - chat_logs: Timestamped queries and AI responses
    - documents: Linked reference materials
    - anomaly_reports: User-flagged issues and audit trails
    - audit_trail: Immutable logs of system-level actions

  NOTES:
    - All timestamps default to CURRENT_TIMESTAMP
    - Foreign keys enforce referential integrity
    - Designed for PostgreSQL 13–18 compatibility
    - ERD available via pgAdmin 4’s ERD Tool

===========================================================
*/

-- Database: cascade_freight_system

-- DROP DATABASE IF EXISTS cascade_freight_system;

CREATE DATABASE cascade_freight_system
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'English_United States.1252'
    LC_CTYPE = 'English_United States.1252'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

COMMENT ON DATABASE cascade_freight_system
    IS 'Database for Secure, on-premise chatbot system for Cascade Freight Systems. Includes modules for user authentication, chat logging, anomaly reporting, document tracking, and audit trails. Designed for modular expansion and PostgreSQL 13–18 compatibility.';

GRANT TEMPORARY, CONNECT ON DATABASE cascade_freight_system TO PUBLIC;

GRANT ALL ON DATABASE cascade_freight_system TO admin_team WITH GRANT OPTION;

GRANT ALL ON DATABASE cascade_freight_system TO postgres;

GRANT CONNECT ON DATABASE cascade_freight_system TO readonly WITH GRANT OPTION;

-- Step 1: Create users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    role VARCHAR(20) CHECK (role IN ('admin', 'agent', 'auditor')),
    mfa_enabled BOOLEAN DEFAULT FALSE,
    email VARCHAR(100) UNIQUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 2: Add index for login performance (optional but recommended)
CREATE UNIQUE INDEX idx_users_username ON users(username);

INSERT INTO users (username, hashed_password, role, mfa_enabled, email)
VALUES 
  ('admin1', 'hashed_admin_pw', 'admin', TRUE, 'admin1@cascadefreight.com'),
  ('agent_jane', 'hashed_agent_pw', 'agent', FALSE, 'jane@cascadefreight.com'),
  ('auditor_bob', 'hashed_auditor_pw', 'auditor', TRUE, 'bob@cascadefreight.com');


-- Step 3: Create chat_logs table
-- Purpose: Stores chatbot interactions for audit, analytics, and anomaly detection

CREATE TABLE chat_logs (
    log_id SERIAL PRIMARY KEY,  -- Unique identifier for each chat interaction
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,  -- Links to the user who initiated the query; cascades on user deletion
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- When the interaction occurred
    query TEXT,  -- The user's input to the chatbot
    response TEXT,  -- The chatbot's reply
    flagged BOOLEAN DEFAULT FALSE,  -- Marks the interaction for review (e.g., inappropriate, anomalous)
    log_type VARCHAR(20) CHECK (log_type IN ('auth', 'document', 'anomaly', 'general')),  -- Categorizes the type of interaction
    response_time_ms INTEGER  -- Time taken to generate the response (in milliseconds)
);

INSERT INTO chat_logs (
  user_id,
  query,
  response,
  timestamp,
  flagged,
  log_type,
  response_time_ms
)
VALUES (
  2,
  'Checked in shipment AD400',
  'Shipment AD400 confirmed and logged.',
  CURRENT_TIMESTAMP,
  FALSE,
  'document',
  120
);

-- Chat log 1
INSERT INTO chat_logs (
  user_id,
  query,
  response,
  timestamp,
  flagged,
  log_type,
  response_time_ms
)
VALUES (
  2,
  'Checked in shipment AD400',
  'Shipment AD400 confirmed and logged.',
  CURRENT_TIMESTAMP,
  FALSE,
  'document',
  120
);

-- Chat log 2
INSERT INTO chat_logs (
  user_id,
  query,
  response,
  timestamp,
  flagged,
  log_type,
  response_time_ms
)
VALUES (
  3,
  'Login attempt failed twice',
  'Please verify MFA settings and try again.',
  CURRENT_TIMESTAMP,
  TRUE,
  'auth',
  300
);

-- Chat log 3
INSERT INTO chat_logs (
  user_id,
  query,
  response,
  timestamp,
  flagged,
  log_type,
  response_time_ms
)
VALUES (
  1,
  'Cannot access AD400 SOP',
  'Access level mismatch detected. Admin override required.',
  CURRENT_TIMESTAMP,
  TRUE,
  'document',
  250
);


-- Optional indexes for performance
-- CREATE INDEX idx_chat_logs_user_id ON chat_logs(user_id);
-- CREATE INDEX idx_chat_logs_flagged ON chat_logs(flagged);


-- Step 4: Create documents table
-- Purpose: Stores metadata and secure access links for chatbot-related documents.
-- Includes classification, ownership, and audit timestamps.

CREATE TABLE documents (
    doc_id SERIAL PRIMARY KEY,  -- Unique identifier for each document
    title VARCHAR(100),  -- Human-readable title of the document
    doc_type VARCHAR(50) CHECK (doc_type IN ('policy', 'report', 'manual', 'contract')),  -- Classification of document type
    secure_link TEXT,  -- Encrypted or access-controlled link to the document
    last_updated TIMESTAMP,  -- Timestamp of the last update to the document
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Timestamp when the document record was created
    owner_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL  -- Links to the user who owns the document; nullifies if user is deleted
);

INSERT INTO documents (
  title,
  doc_type,
  secure_link,
  last_updated,
  owner_id
)
VALUES (
  'AD400 SOP',
  'manual',
  'https://secure.cascadefreight.com/docs/ad400_sop.pdf',
  CURRENT_TIMESTAMP,
  1
);


-- Step 5: Create anomaly_reports table
-- Purpose: Tracks flagged chatbot interactions requiring review, escalation, or resolution.
-- Links each report to the originating user and chat log entry.

CREATE TABLE anomaly_reports (
    report_id SERIAL PRIMARY KEY,  -- Unique identifier for each anomaly report
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,  -- User who triggered the anomaly; nullified if user is deleted
    log_id INTEGER REFERENCES chat_logs(log_id) ON DELETE CASCADE,  -- Chat log entry associated with the anomaly; cascades if log is deleted
    description TEXT,  -- Detailed explanation of the anomaly or issue
    status VARCHAR(20) CHECK (status IN ('open', 'in_review', 'resolved', 'dismissed')),  -- Current state of the report
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Timestamp when the report was created
);

-- Report 1: Open anomaly linked to chat log 1 by user 2
INSERT INTO anomaly_reports (
  user_id,
  log_id,
  description,
  status
)
VALUES (
  2,
  1,
  'Barcode missing on incoming shipment AD400',
  'open'
);

-- Report 2: In review anomaly linked to chat log 2 by user 3
INSERT INTO anomaly_reports (
  user_id,
  log_id,
  description,
  status
)
VALUES (
  3,
  2,
  'Authentication delay flagged during login attempt',
  'in_review'
);

-- Report 3: Resolved anomaly linked to chat log 3 by user 1
INSERT INTO anomaly_reports (
  user_id,
  log_id,
  description,
  status
)
VALUES (
  1,
  3,
  'Document access level mismatch resolved by admin override',
  'resolved'
);

-- Step 6: Create audit_trail table
-- Purpose: Logs user actions across the system for traceability, compliance, and forensic analysis.

CREATE TABLE audit_trail (
    event_id SERIAL PRIMARY KEY,  -- Unique identifier for each audit event
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,  -- User who performed the action; nullified if user is deleted
    action VARCHAR(100),  -- Description of the action taken (e.g., 'login', 'document_access', 'flag_resolved')
    target VARCHAR(100),  -- The object or entity affected by the action (e.g., 'doc_42', 'log_17')
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- When the action occurred
    integrity_hash TEXT  -- Optional hash to verify the integrity of the event record
);

-- Admin created a document
INSERT INTO audit_trail (
  user_id,
  action,
  target,
  integrity_hash
)
VALUES (
  1,
  'document_created',
  'doc_1',
  'hash_abc123'
);

-- Agent accessed a document
INSERT INTO audit_trail (
  user_id,
  action,
  target,
  integrity_hash
)
VALUES (
  2,
  'document_access',
  'doc_1',
  'hash_def456'
);

-- Customer triggered anomaly flag
INSERT INTO audit_trail (
  user_id,
  action,
  target,
  integrity_hash
)
VALUES (
  3,
  'flag_triggered',
  'log_2',
  'hash_xyz789'
);

-- Admin resolved anomaly
INSERT INTO audit_trail (
  user_id,
  action,
  target,
  integrity_hash
)
VALUES (
  1,
  'flag_resolved',
  'report_3',
  'hash_res123'
);

-- Auditor reviewed login event
INSERT INTO audit_trail (
  user_id,
  action,
  target,
  integrity_hash
)
VALUES (
  3,
  'login_reviewed',
  'log_2',
  'hash_audit321'
);

INSERT INTO audit_trail (
  user_id,
  action,
  target,
  integrity_hash
)
VALUES (
  NULL,
  'keyboard_disruption',
  'project_milestone_2',
  'hash_ritzi_pawprint_001'
);

-- ===========================================================
-- MODULE: Dispatch & Shipment Tracking (BRD Sections 2.0–3.0)
-- PURPOSE: Supports driver lookup, shipment status, ETA updates, and reassignment logging
-- ===========================================================

-- Step 7: Create drivers table
CREATE TABLE drivers (
    driver_id SERIAL PRIMARY KEY,
    employee_name VARCHAR(100),
    license_number VARCHAR(50),
    status VARCHAR(20) CHECK (status IN ('on_duty', 'en_route', 'idle')),
    last_known_location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 8: Create shipments table
CREATE TABLE shipments (
    shipment_id SERIAL PRIMARY KEY,
    origin VARCHAR(100),
    destination VARCHAR(100),
    status VARCHAR(20) CHECK (status IN ('pending', 'in_transit', 'delivered')),
    eta TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 9: Create assignments table
CREATE TABLE assignments (
    assignment_id SERIAL PRIMARY KEY,
    driver_id INTEGER REFERENCES drivers(driver_id) ON DELETE CASCADE,
    shipment_id INTEGER REFERENCES shipments(shipment_id) ON DELETE CASCADE,
    date_assigned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reassignment_reason TEXT
);
