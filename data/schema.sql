-- Banking Control Solution — SQLite warehouse (demo)

CREATE TABLE IF NOT EXISTS DIM_BUSINESS_UNIT (
  unit_id INTEGER PRIMARY KEY,
  unit_code TEXT NOT NULL UNIQUE,
  unit_name TEXT NOT NULL,
  region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS DIM_CONTROL (
  control_id INTEGER PRIMARY KEY,
  control_code TEXT NOT NULL UNIQUE,
  control_name TEXT NOT NULL,
  domain TEXT NOT NULL,
  risk_tier TEXT NOT NULL CHECK (risk_tier IN ('Critical', 'High', 'Medium', 'Low')),
  owner TEXT NOT NULL,
  frequency TEXT NOT NULL,
  description TEXT NOT NULL,
  is_golden INTEGER NOT NULL DEFAULT 0,
  similarity_key TEXT,
  standards_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_control_similarity ON DIM_CONTROL(similarity_key);
CREATE INDEX IF NOT EXISTS idx_control_golden ON DIM_CONTROL(is_golden);

CREATE TABLE IF NOT EXISTS FCT_CONTROL_ASSESSMENT (
  assessment_id INTEGER PRIMARY KEY,
  control_id INTEGER NOT NULL REFERENCES DIM_CONTROL(control_id),
  unit_id INTEGER NOT NULL REFERENCES DIM_BUSINESS_UNIT(unit_id),
  assessment_date TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('Effective', 'Partially Effective', 'Ineffective', 'Not Tested')),
  tester TEXT NOT NULL,
  evidence_ref TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS FCT_EXCEPTION (
  exception_id INTEGER PRIMARY KEY,
  control_id INTEGER NOT NULL REFERENCES DIM_CONTROL(control_id),
  unit_id INTEGER NOT NULL REFERENCES DIM_BUSINESS_UNIT(unit_id),
  opened_at TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('Critical', 'High', 'Medium', 'Low')),
  status TEXT NOT NULL CHECK (status IN ('Open', 'In Remediation', 'Pending Validation', 'Closed')),
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  assignee TEXT NOT NULL,
  due_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS FCT_TRANSACTION_ALERT (
  alert_id INTEGER PRIMARY KEY,
  unit_id INTEGER NOT NULL REFERENCES DIM_BUSINESS_UNIT(unit_id),
  alert_at TEXT NOT NULL,
  alert_type TEXT NOT NULL,
  amount_usd REAL NOT NULL,
  customer_ref TEXT NOT NULL,
  channel TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('New', 'Under Review', 'Escalated', 'Cleared', 'SAR Filed')),
  risk_score REAL NOT NULL,
  narrative TEXT NOT NULL,
  alert_origin TEXT NOT NULL DEFAULT 'historical' CHECK (alert_origin IN ('historical', 'live'))
);

CREATE TABLE IF NOT EXISTS FCT_AUDIT_EVENT (
  event_id INTEGER PRIMARY KEY,
  event_at TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  detail TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS APP_OVERVIEW_SNAPSHOT (
  snapshot_key TEXT PRIMARY KEY,
  payload_json TEXT NOT NULL,
  refreshed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS APP_ADMIN_LLM (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  provider_type TEXT NOT NULL DEFAULT 'bedrock',
  bedrock_region TEXT,
  bedrock_model_id TEXT,
  bedrock_max_tokens INTEGER,
  bedrock_temperature REAL,
  openai_base_url TEXT,
  openai_model_id TEXT,
  openai_api_token TEXT,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS FCT_CONTROL_WORKFLOW (
  workflow_id INTEGER PRIMARY KEY,
  control_id INTEGER NOT NULL REFERENCES DIM_CONTROL(control_id),
  workflow_type TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('Draft', 'In Progress', 'Complete', 'Cancelled')),
  artifact_ref TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_assessment_control ON FCT_CONTROL_ASSESSMENT(control_id);
CREATE INDEX IF NOT EXISTS idx_workflow_control ON FCT_CONTROL_WORKFLOW(control_id);
CREATE INDEX IF NOT EXISTS idx_exception_status ON FCT_EXCEPTION(status);
CREATE INDEX IF NOT EXISTS idx_alert_status ON FCT_TRANSACTION_ALERT(status);
