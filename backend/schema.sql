-- Foundation schema 7. Fresh bootstrap only: never migrate or overwrite old data.
CREATE TABLE tenants (id TEXT PRIMARY KEY, active_release TEXT);
CREATE TABLE review_snapshots (
 tenant_id TEXT NOT NULL REFERENCES tenants(id), id TEXT NOT NULL,
 sha256 TEXT NOT NULL, config TEXT NOT NULL CHECK(json_valid(config)),
 PRIMARY KEY(tenant_id,id)
);
CREATE TABLE review_records (
 tenant_id TEXT NOT NULL REFERENCES tenants(id), id TEXT NOT NULL,
 snapshot_id TEXT NOT NULL, report_text TEXT NOT NULL, input_hash TEXT NOT NULL,
 created_at TEXT NOT NULL, completed_at TEXT, input_version INTEGER NOT NULL DEFAULT 1,
 execution_status TEXT NOT NULL CHECK(execution_status IN ('queued','running','completed','needs_input','failed')),
 steps TEXT NOT NULL CHECK(json_valid(steps)), provenance TEXT NOT NULL CHECK(json_valid(provenance)),
 error TEXT CHECK(error IS NULL OR json_valid(error)), api_version TEXT NOT NULL,
 PRIMARY KEY(tenant_id,id), UNIQUE(id),
 FOREIGN KEY(tenant_id,snapshot_id) REFERENCES review_snapshots(tenant_id,id)
);
CREATE INDEX review_history ON review_records(tenant_id,created_at,id);
CREATE INDEX review_dispatch ON review_records(execution_status,tenant_id,id);
CREATE TABLE review_results (
 tenant_id TEXT NOT NULL, review_id TEXT NOT NULL, result_version INTEGER NOT NULL CHECK(result_version>0),
 metadata TEXT NOT NULL CHECK(json_valid(metadata)),
 PRIMARY KEY(tenant_id,review_id), UNIQUE(tenant_id,review_id,result_version),
 FOREIGN KEY(tenant_id,review_id) REFERENCES review_records(tenant_id,id)
);
CREATE TABLE observations (
 tenant_id TEXT NOT NULL, review_id TEXT NOT NULL, result_version INTEGER NOT NULL,
 id TEXT NOT NULL, group_name TEXT NOT NULL CHECK(group_name IN ('general_comments','critical_comments')),
 position INTEGER NOT NULL CHECK(position>=0), document TEXT NOT NULL CHECK(json_valid(document)),
 PRIMARY KEY(tenant_id,review_id,result_version,id),
 UNIQUE(tenant_id,review_id,group_name,position),
 FOREIGN KEY(tenant_id,review_id,result_version) REFERENCES review_results(tenant_id,review_id,result_version)
);
CREATE TABLE feedback (
 tenant_id TEXT NOT NULL, id TEXT NOT NULL, review_id TEXT NOT NULL,
 document TEXT NOT NULL CHECK(json_valid(document)), schema_version INTEGER NOT NULL CHECK(schema_version=7),
 PRIMARY KEY(tenant_id,id), UNIQUE(id),
 FOREIGN KEY(tenant_id,review_id) REFERENCES review_records(tenant_id,id)
);
CREATE INDEX feedback_review_order ON feedback(tenant_id,review_id);
-- Retired compatibility storage only. No outcome API or analytics reads remain.
CREATE TABLE outcomes (
 tenant_id TEXT NOT NULL, id TEXT NOT NULL, review_id TEXT NOT NULL,
 document TEXT NOT NULL CHECK(json_valid(document)),
 result_version INTEGER GENERATED ALWAYS AS (json_extract(document,'$.result_version')) STORED NOT NULL,
 PRIMARY KEY(tenant_id,id),
 FOREIGN KEY(tenant_id,review_id,result_version) REFERENCES review_results(tenant_id,review_id,result_version)
);
CREATE INDEX outcomes_review ON outcomes(tenant_id,review_id);
-- A named tenant draft of a whole pack. It can be composed and run; it never serves live QA.
-- forked_release/forked_content_sha256 pin the published pack this workspace was taken from, so
-- a diff computed against a pack that has since moved is detectable rather than silently wrong.
CREATE TABLE skill_workspaces (
 tenant_id TEXT NOT NULL REFERENCES tenants(id), id TEXT NOT NULL,
 name TEXT NOT NULL, created_at TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('open','submitted','published','closed')),
 forked_release TEXT NOT NULL, forked_content_sha256 TEXT NOT NULL,
 submitted_at TEXT, summary TEXT,
 PRIMARY KEY(tenant_id,id)
);
-- workspace_id '' is an editorial draft that belongs to no workspace and never composes.
-- A non-empty value is validated in code against skill_workspaces; SQLite cannot express a
-- foreign key that tolerates the sentinel.
CREATE TABLE knowledge_drafts (
 tenant_id TEXT NOT NULL REFERENCES tenants(id), workspace_id TEXT NOT NULL DEFAULT '',
 document_id TEXT NOT NULL,
 revision INTEGER NOT NULL CHECK(revision>0), id TEXT NOT NULL,
 document TEXT NOT NULL CHECK(json_valid(document)),
 PRIMARY KEY(tenant_id,workspace_id,document_id,revision), UNIQUE(tenant_id,id)
);
-- Playground runs are written only here. They never enter review_records, review_results or
-- observations, and analytics, feedback and outcomes never read this table. There is no
-- history surface: a run is reachable only from the screen that started it.
CREATE TABLE playground_runs (
 tenant_id TEXT NOT NULL REFERENCES tenants(id), id TEXT NOT NULL,
 pack_ref TEXT NOT NULL, release_id TEXT NOT NULL,
 source TEXT NOT NULL CHECK(source IN ('sample','pasted')),
 sample_id TEXT, report_text TEXT NOT NULL, model TEXT NOT NULL, mode TEXT NOT NULL,
 created_at TEXT NOT NULL, completed_at TEXT,
 status TEXT NOT NULL CHECK(status IN ('queued','running','completed','needs_input','failed')),
 steps TEXT NOT NULL CHECK(json_valid(steps)),
 result TEXT CHECK(result IS NULL OR json_valid(result)),
 error TEXT CHECK(error IS NULL OR json_valid(error)),
 PRIMARY KEY(tenant_id,id)
);
CREATE INDEX playground_recent ON playground_runs(tenant_id,created_at,id);
-- The live checkpoint table references review_records, so a playground run cannot use it.
-- Same shape and same rules: a claim without a durable response is never retried automatically.
-- review_id holds the playground run id so one implementation serves both tables.
CREATE TABLE playground_attempts (
 tenant_id TEXT NOT NULL, review_id TEXT NOT NULL, attempt_id TEXT NOT NULL UNIQUE,
 outcome TEXT NOT NULL CHECK(outcome IN ('claimed','response','unknown')),
 response TEXT CHECK(response IS NULL OR json_valid(response)),
 PRIMARY KEY(tenant_id,review_id),
 FOREIGN KEY(tenant_id,review_id) REFERENCES playground_runs(tenant_id,id)
);
CREATE TRIGGER playground_attempt_response_immutable BEFORE UPDATE ON playground_attempts
WHEN OLD.outcome='response'
BEGIN SELECT RAISE(ABORT,'Provider response checkpoint is immutable'); END;
CREATE TABLE idempotency (
 tenant_id TEXT NOT NULL REFERENCES tenants(id), operation TEXT NOT NULL,
 key_hash TEXT NOT NULL, request_hash TEXT NOT NULL, api_version TEXT NOT NULL,
 response TEXT NOT NULL CHECK(json_valid(response)), created_at TEXT NOT NULL,
 PRIMARY KEY(tenant_id,operation,key_hash)
);
-- Application-owned read projection, not a persisted public API document. Existing
-- reporting modules share this view; writes use normalized tables and constraints.
CREATE VIEW reviews AS
SELECT r.rowid AS rowid, r.tenant_id, r.id,
 json_object('report_text',r.report_text) AS request, s.config,
 json_object(
  'tenant_id',r.tenant_id,'review_id',r.id,'created_at',r.created_at,
  'completed_at',r.completed_at,'input_version',r.input_version,'input_hash',r.input_hash,
  'input',json_object('report_text',r.report_text),'execution_status',r.execution_status,
  'steps',json(r.steps),'provenance',json(r.provenance),'error',json(r.error),
  'result',json(CASE WHEN x.review_id IS NULL THEN NULL ELSE
   json_patch(x.metadata,json_object(
    'general_comments',json((SELECT json_group_array(json(document)) FROM
      (SELECT document FROM observations o WHERE o.tenant_id=r.tenant_id AND o.review_id=r.id AND o.group_name='general_comments' ORDER BY position))),
    'critical_comments',json((SELECT json_group_array(json(document)) FROM
      (SELECT document FROM observations o WHERE o.tenant_id=r.tenant_id AND o.review_id=r.id AND o.group_name='critical_comments' ORDER BY position)))
   )) END)
 ) AS document
FROM review_records r
JOIN review_snapshots s ON s.tenant_id=r.tenant_id AND s.id=r.snapshot_id
LEFT JOIN review_results x ON x.tenant_id=r.tenant_id AND x.review_id=r.id;
CREATE TRIGGER snapshot_immutable BEFORE UPDATE ON review_snapshots
BEGIN SELECT RAISE(ABORT,'Accepted snapshot is immutable'); END;
CREATE TRIGGER result_immutable BEFORE UPDATE ON review_results
BEGIN SELECT RAISE(ABORT,'Completed result is immutable'); END;
CREATE TRIGGER observation_immutable BEFORE UPDATE ON observations
BEGIN SELECT RAISE(ABORT,'Completed observation is immutable'); END;
CREATE TABLE model_attempts (
 tenant_id TEXT NOT NULL, review_id TEXT NOT NULL, attempt_id TEXT NOT NULL UNIQUE,
 outcome TEXT NOT NULL CHECK(outcome IN ('claimed','response','unknown')),
 response TEXT CHECK(response IS NULL OR json_valid(response)),
 PRIMARY KEY(tenant_id,review_id),
 FOREIGN KEY(tenant_id,review_id) REFERENCES review_records(tenant_id,id)
);
CREATE TRIGGER attempt_response_immutable BEFORE UPDATE ON model_attempts
WHEN OLD.outcome='response'
BEGIN SELECT RAISE(ABORT,'Provider response checkpoint is immutable'); END;
