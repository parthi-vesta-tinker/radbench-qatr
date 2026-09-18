-- Foundation schema 4. Fresh bootstrap only: never migrate or overwrite old data.
CREATE TABLE tenants (id TEXT PRIMARY KEY, active_release TEXT);
CREATE TABLE review_snapshots (
 tenant_id TEXT NOT NULL REFERENCES tenants(id), id TEXT NOT NULL,
 sha256 TEXT NOT NULL, config TEXT NOT NULL CHECK(json_valid(config)),
 PRIMARY KEY(tenant_id,id)
);
CREATE TABLE review_records (
 tenant_id TEXT NOT NULL REFERENCES tenants(id), id TEXT NOT NULL,
 snapshot_id TEXT NOT NULL, report_text TEXT NOT NULL, input_hash TEXT NOT NULL,
 created_at TEXT NOT NULL, completed_at TEXT,
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
 document TEXT NOT NULL CHECK(json_valid(document)), schema_version INTEGER NOT NULL CHECK(schema_version=4),
 result_version INTEGER GENERATED ALWAYS AS (json_extract(document,'$.result_version')) STORED NOT NULL,
 observation_id TEXT GENERATED ALWAYS AS (json_extract(document,'$.observation_id')) STORED,
 PRIMARY KEY(tenant_id,id), UNIQUE(id),
 FOREIGN KEY(tenant_id,review_id,result_version) REFERENCES review_results(tenant_id,review_id,result_version),
 FOREIGN KEY(tenant_id,review_id,result_version,observation_id) REFERENCES observations(tenant_id,review_id,result_version,id)
);
CREATE INDEX feedback_review_order ON feedback(tenant_id,review_id);
CREATE TABLE outcomes (
 tenant_id TEXT NOT NULL, id TEXT NOT NULL, review_id TEXT NOT NULL,
 document TEXT NOT NULL CHECK(json_valid(document)),
 result_version INTEGER GENERATED ALWAYS AS (json_extract(document,'$.result_version')) STORED NOT NULL,
 PRIMARY KEY(tenant_id,id),
 FOREIGN KEY(tenant_id,review_id,result_version) REFERENCES review_results(tenant_id,review_id,result_version)
);
CREATE INDEX outcomes_review ON outcomes(tenant_id,review_id);
CREATE TABLE knowledge_drafts (
 tenant_id TEXT NOT NULL REFERENCES tenants(id), document_id TEXT NOT NULL,
 revision INTEGER NOT NULL CHECK(revision>0), id TEXT NOT NULL,
 document TEXT NOT NULL CHECK(json_valid(document)),
 PRIMARY KEY(tenant_id,document_id,revision), UNIQUE(tenant_id,id)
);
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
  'completed_at',r.completed_at,'input_version',1,'input_hash',r.input_hash,
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
CREATE TRIGGER review_input_immutable BEFORE UPDATE OF report_text,input_hash,snapshot_id,tenant_id,id,created_at ON review_records
BEGIN SELECT RAISE(ABORT,'Accepted input is immutable'); END;
CREATE TRIGGER review_terminal_immutable BEFORE UPDATE ON review_records
WHEN OLD.execution_status IN ('completed','failed','needs_input')
BEGIN SELECT RAISE(ABORT,'Terminal review is immutable'); END;
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
