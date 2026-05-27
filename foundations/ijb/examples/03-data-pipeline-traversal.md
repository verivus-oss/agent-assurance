# Example 03: Data Pipeline Traversal

A single path following customer transaction data through ingestion, transformation, validation, and loading into a data warehouse.

## The Scenario

A scheduled batch of customer transaction records moves through a data pipeline with multiple transformation stages, quality gates, partial failures, and retry paths.

This example demonstrates:
- Data as a thing moving through processing stages
- Quality constraints as gates (pass/fail decisions)
- Partial success (some records proceed, some fail)
- Retry paths for failed records
- Resource constraints (memory, compute)
- Multiple technical scopes (ingestion, transformation, storage, serving)
- Time dimension (scheduled runs, processing duration, SLA deadlines)

---

## Part 1: Factual Description

### Things That Exist

```
Dataset-Batch-20241210-0600     # Batch identifier (scheduled run)
Raw-Records-347829              # Aggregate of 347,829 transaction records (source)
S3-Landing-Zone                 # S3 bucket: raw-data-landing/
Ingestion-Service               # Python service: data-ingestion-v2
Kafka-Topic-Raw-Txns            # Kafka topic: raw-transactions
Spark-Job-Transform-8847        # Spark job execution ID
Validation-Service              # Data quality validation service
Valid-Records-342105            # 342,105 records passing validation
Invalid-Records-5724            # 5,724 records failing validation
S3-Quarantine-Zone              # S3 bucket: quarantine/
Transformed-Records-342105      # 342,105 enriched records
Redshift-Staging-Table          # staging.transactions_20241210
Redshift-Production-Table       # prod.transactions (final destination)
DBT-Job-Merge-5521              # DBT transformation job
Airflow-DAG-Run-Daily-Txns      # Airflow orchestration run
CloudWatch-Metrics              # AWS CloudWatch monitoring
PagerDuty-Alert-5848            # Alert for validation failure spike
Looker-Dashboard-Daily-Revenue  # Analytics dashboard waiting for data

Sarah Park                      # Data Engineer (on-call)
Alex Chen                       # Data Analyst (consumer of pipeline output)
Database-Platform-Team          # Infrastructure team (4 members)

Retry-Records-5724              # Failed records queued for retry
Retry-Job-Transform-8848        # Second Spark job for retries
Recovered-Records-4891          # 4,891 records successful on retry
Failed-Final-Records-833        # 833 records failing after retry
```

### Scopes Where Things Exist

```
AWS-US-East-1                   # Cloud region
Data-Landing-Zone               # Raw data ingestion scope
Data-Processing-Zone            # Transformation scope
Data-Storage-Zone               # Warehouse scope
Data-Serving-Zone               # Analytics consumption scope

S3-Storage-Layer                # Object storage
Kafka-Streaming-Layer           # Message streaming
Spark-Compute-Layer             # Distributed processing
Redshift-Warehouse-Layer        # Analytical database

Data-Engineering-Team           # Organizational scope
Analytics-Team                  # Organizational scope
Platform-Team                   # Organizational scope

Scheduled-Batch-Window          # Temporal scope: Daily 06:00-09:00 EST
Business-Hours                  # Temporal scope: 09:00-18:00 EST
SLA-Deadline-09:00              # Data must be available by 9am EST

Quality-Validated-State         # State scope: records passing quality checks
Quality-Failed-State            # State scope: records failing quality checks
Processing-State                # State scope: records in transformation
Complete-State                  # State scope: records in production table
```

### Paths That Connect Things

```
Path 1: Ingestion → Streaming
  Raw-Records-347829 moves from External-Source → S3-Landing-Zone
  Raw-Records-347829 moves from S3-Landing-Zone → Ingestion-Service
  Raw-Records-347829 moves from Ingestion-Service → Kafka-Topic-Raw-Txns

Path 2: Streaming → Processing
  Raw-Records-347829 moves from Kafka-Topic-Raw-Txns → Spark-Job-Transform-8847

Path 3: Processing → Validation (Split)
  Raw-Records-347829 enters Validation-Service
  Valid-Records-342105 moves from Validation-Service → Transformed-Records-342105
  Invalid-Records-5724 moves from Validation-Service → S3-Quarantine-Zone
  Invalid-Records-5724 moves from Validation-Service → Retry-Records-5724 (queued)

Path 4: Loading → Production
  Transformed-Records-342105 moves from Spark-Job-Transform-8847 → Redshift-Staging-Table
  Transformed-Records-342105 moves from Redshift-Staging-Table → Redshift-Production-Table
  Data-Available notification moves from DBT-Job-Merge-5521 → Looker-Dashboard-Daily-Revenue

Path 5: Monitoring → Alert
  Validation failure metrics move from Validation-Service → CloudWatch-Metrics
  Alert moves from CloudWatch-Metrics → PagerDuty-Alert-5848
  Page moves from PagerDuty-Alert-5848 → Sarah Park

Path 6: Retry Path
  Retry-Records-5724 moves from S3-Quarantine-Zone → Spark-Job-Transform-8848 (retry job)
  Retry-Records-5724 enters Validation-Service (second attempt)
  Recovered-Records-4891 moves from Validation-Service → Redshift-Staging-Table
  Failed-Final-Records-833 moves from Validation-Service → S3-Quarantine-Zone (permanent)

Path 7: Communication
  Assessment moves from Sarah Park → Analytics-Team (via Slack)
  Status update moves from Sarah Park → Alex Chen
```

### Observations Made

```
2024-12-10T06:00:00Z - Airflow-DAG-Run-Daily-Txns triggered (scheduled)
2024-12-10T06:00:15Z - Raw-Records-347829 arrived at S3-Landing-Zone (size: 4.2GB)
2024-12-10T06:01:30Z - Ingestion-Service started reading from S3
2024-12-10T06:04:45Z - Raw-Records-347829 published to Kafka-Topic-Raw-Txns (complete)
2024-12-10T06:05:00Z - Spark-Job-Transform-8847 started (allocated 20 executors)
2024-12-10T06:08:15Z - Spark-Job-Transform-8847 completed read phase (347,829 records)
2024-12-10T06:11:30Z - Validation-Service processing started
2024-12-10T06:14:45Z - Validation-Service completed
                       - Valid-Records-342105 (98.35% pass rate)
                       - Invalid-Records-5724 (1.65% failure rate)
2024-12-10T06:15:00Z - Invalid-Records-5724 written to S3-Quarantine-Zone
2024-12-10T06:15:30Z - CloudWatch-Metrics: validation_failure_rate = 1.65%
2024-12-10T06:15:45Z - PagerDuty-Alert-5848 triggered (threshold: 1.5%, observed: 1.65%)
2024-12-10T06:17:00Z - Sarah Park acknowledged alert
2024-12-10T06:18:30Z - Transformed-Records-342105 write to Redshift-Staging-Table started
2024-12-10T06:23:45Z - Transformed-Records-342105 write completed (342,105 rows inserted)
2024-12-10T06:24:00Z - DBT-Job-Merge-5521 started
2024-12-10T06:27:15Z - DBT-Job-Merge-5521 completed (342,105 rows merged into prod.transactions)
2024-12-10T06:27:30Z - Looker-Dashboard-Daily-Revenue data refresh triggered
2024-12-10T06:28:00Z - Looker-Dashboard-Daily-Revenue shows new data available
2024-12-10T06:30:00Z - Alex Chen accesses dashboard (data available before SLA deadline)

[Parallel retry path]

2024-12-10T06:20:00Z - Sarah Park triggered manual retry for Invalid-Records-5724
2024-12-10T06:20:30Z - Spark-Job-Transform-8848 started (retry job, 10 executors)
2024-12-10T06:22:00Z - Retry-Records-5724 read from S3-Quarantine-Zone
2024-12-10T06:24:30Z - Validation-Service processing retry batch
2024-12-10T06:26:00Z - Validation-Service completed retry
                       - Recovered-Records-4891 (85.4% recovery rate)
                       - Failed-Final-Records-833 (14.6% permanent failure)
2024-12-10T06:26:30Z - Recovered-Records-4891 written to Redshift-Staging-Table
2024-12-10T06:29:00Z - DBT-Job-Merge-5521 (incremental) merged Recovered-Records-4891
2024-12-10T06:29:30Z - Final state: 346,996 records in production (99.76% of original batch)
2024-12-10T06:30:00Z - Failed-Final-Records-833 written to S3-Quarantine-Zone/permanent/
2024-12-10T06:31:00Z - Sarah Park posted analysis to Slack: "833 records failed schema validation"

[Later observations]

2024-12-10T09:15:00Z - Alex Chen ran analysis query on prod.transactions
2024-12-10T09:17:00Z - Query completed (scanned 346,996 new rows)
```

### Constraints That Apply

```
Constraint 1: SLA deadline - data available by 09:00 EST
  Type: Time-based service level agreement
  Scope: Redshift-Production-Table availability
  Threshold: 09:00:00 EST
  Observed: Data available at 06:27:30 EST (2h32m30s before deadline)
  Status: Satisfied

Constraint 2: Data quality - validation failure rate < 1.5%
  Type: Quality threshold
  Scope: Validation-Service
  Threshold: 1.5%
  Observed: 1.65% (initial batch)
  Status: Violated (triggered alert)

Constraint 3: Record completeness - all fields required
  Type: Schema validation
  Scope: Validation-Service
  Required: customer_id, transaction_id, amount, timestamp, currency
  Observed: 5,724 records missing required fields (initial)
  Observed: 833 records missing required fields (after retry)
  Status: Failed records quarantined

Constraint 4: Data freshness - source data < 6 hours old
  Type: Temporal constraint
  Scope: Raw-Records-347829
  Threshold: 6 hours from transaction time
  Observed: All records within 4 hours of transaction time
  Status: Satisfied

Constraint 5: Processing window - complete within 3 hours
  Type: Time window
  Scope: Entire pipeline (ingestion → production)
  Threshold: 3 hours
  Observed: 29 minutes 30 seconds (main path), 29 minutes (retry path)
  Status: Satisfied

Constraint 6: Spark cluster resources - max 50 executors
  Type: Resource limit
  Scope: Spark-Compute-Layer
  Threshold: 50 executors
  Observed: 20 executors (main job), 10 executors (retry job)
  Status: Satisfied

Constraint 7: Redshift write rate - max 100K rows/minute
  Type: Throughput limit
  Scope: Redshift-Staging-Table
  Threshold: 100,000 rows/minute
  Observed: 65,163 rows/minute (342,105 rows in 5m15s)
  Status: Satisfied

Constraint 8: Retry policy - one retry attempt for failed records
  Type: Processing policy
  Scope: Invalid-Records-5724
  Max retries: 1
  Observed: 1 retry executed
  Status: Satisfied (no further retries for Failed-Final-Records-833)

Constraint 9: Data at rest encryption required
  Type: Security policy
  Scope: S3-Landing-Zone, S3-Quarantine-Zone, Redshift-Production-Table
  Observed: AES-256 encryption confirmed on all storage
  Status: Satisfied
```

### Time Ordering

```
Timeline (Total pipeline duration: 31 minutes, including parallel retry)

Main Path:
T+0:00      (06:00:00) - Scheduled trigger (Airflow DAG)
T+0:15      (06:00:15) - Data lands in S3 (347,829 records, 4.2GB)
T+1:30      (06:01:30) - Ingestion service begins reading
T+4:45      (06:04:45) - Data published to Kafka (complete)
T+5:00      (06:05:00) - Spark job starts transformation
T+8:15      (06:08:15) - Read phase complete
T+11:30     (06:11:30) - Validation begins
T+14:45     (06:14:45) - Validation complete: 342,105 pass, 5,724 fail
T+15:00     (06:15:00) - Failed records written to quarantine
T+15:30     (06:15:30) - Failure rate metric published (1.65%)
T+15:45     (06:15:45) - Alert triggered (exceeded 1.5% threshold)
T+17:00     (06:17:00) - Alert acknowledged
T+18:30     (06:18:30) - Redshift write begins (valid records)
T+23:45     (06:23:45) - Redshift write complete (342,105 rows)
T+24:00     (06:24:00) - DBT merge job starts
T+27:15     (06:27:15) - DBT merge complete (production table updated)
T+27:30     (06:27:30) - Dashboard refresh triggered
T+28:00     (06:28:00) - Dashboard shows new data [SLA satisfied: 2h32m early]

Retry Path (parallel after T+14:45):
T+20:00     (06:20:00) - Manual retry triggered by Sarah Park
T+20:30     (06:20:30) - Retry Spark job starts (5,724 records)
T+22:00     (06:22:00) - Quarantine data read
T+24:30     (06:24:30) - Retry validation begins
T+26:00     (06:26:00) - Retry validation complete: 4,891 recovered, 833 failed
T+26:30     (06:26:30) - Recovered records written to Redshift staging
T+29:00     (06:29:00) - DBT incremental merge (4,891 rows)
T+29:30     (06:29:30) - Final state: 346,996 records in production (99.76% success)
T+30:00     (06:30:00) - Permanent failures quarantined (833 records)
T+31:00     (06:31:00) - Analysis posted to Slack

Post-Pipeline:
T+3:15:00   (09:15:00) - Alex Chen queries production table
T+3:17:00   (09:17:00) - Query completes

Key metrics:
- Ingestion duration: 4m45s (S3 → Kafka)
- Transformation duration: 9m45s (Kafka → Validation complete)
- Loading duration: 12m30s (Validation → Production table)
- Total main path: 27m15s
- Total with retry: 29m30s
- SLA buffer: 2h30m30s (finished 2.5 hours before deadline)
- Success rate: 99.76% (346,996 / 347,829)
- Recovery rate: 85.4% of initially failed records (4,891 / 5,724)
```

---

## Part 2: Spatial Projection Mapping

### Things → Objects in Space

Each thing becomes an object:

```
Dataset-Batch-20241210-0600     → Batch container (large translucent box)
Raw-Records-347829              → Data cluster (347,829 small particles)
S3-Landing-Zone                 → Storage volume (cylinder, green)
Ingestion-Service               → Service object (rotating cube)
Kafka-Topic-Raw-Txns            → Stream channel (flowing ribbon)
Spark-Job-Transform-8847        → Processing cluster (20 small cubes in formation)
Validation-Service              → Gate object (archway with scanner)
Valid-Records-342105            → Data cluster (342,105 particles, green)
Invalid-Records-5724            → Data cluster (5,724 particles, red)
S3-Quarantine-Zone              → Storage volume (cylinder, orange)
Redshift-Staging-Table          → Table object (grid structure, translucent)
Redshift-Production-Table       → Table object (grid structure, solid)
CloudWatch-Metrics              → Monitoring display (dashboard panel)
PagerDuty-Alert-5848            → Alert object (pulsing red icon)
Looker-Dashboard-Daily-Revenue  → Analytics surface (outward-facing screen)

Sarah Park                      → Person object (sphere, blue)
Alex Chen                       → Person object (sphere, purple)

Retry-Records-5724              → Data cluster (5,724 particles, orange → processing)
Recovered-Records-4891          → Data cluster (4,891 particles, orange → green)
Failed-Final-Records-833        → Data cluster (833 particles, dark red)
```

Visual form indicates type and state, not importance or blame.

### Scopes → Spatial Grouping

Scopes become planes, layers, and fields:

```
AWS-US-East-1                   → Entire scene boundary (cloud region outline)

Data-Landing-Zone               → Left vertical plane (z=0)
Data-Processing-Zone            → Center vertical plane (z=5)
Data-Storage-Zone               → Right vertical plane (z=10)
Data-Serving-Zone               → Far right vertical plane (z=15)

S3-Storage-Layer                → Bottom horizontal plane (y=0, green tint)
Kafka-Streaming-Layer           → Lower-mid horizontal plane (y=3, blue tint)
Spark-Compute-Layer             → Upper-mid horizontal plane (y=6, orange tint)
Redshift-Warehouse-Layer        → Top horizontal plane (y=9, purple tint)

Data-Engineering-Team           → Blue circular field around Sarah Park
Analytics-Team                  → Purple circular field around Alex Chen
Platform-Team                   → Gray circular field (infrastructure focus)

Scheduled-Batch-Window          → Temporal indicator: 06:00-09:00 (bright)
SLA-Deadline-09:00              → Red vertical line at x=180min position

Quality-Validated-State         → Green glow overlay
Quality-Failed-State            → Red heat overlay
Processing-State                → Orange animation overlay
Complete-State                  → Solid, stable appearance
```

Data particles appear in multiple scopes as they traverse:
- Raw-Records start in Landing + S3 Layer
- Valid-Records appear in Processing + Spark Layer + Validated-State
- Invalid-Records appear in Quarantine + S3 Layer + Failed-State

### Paths → Routed Connections

Paths become directed flows with data movement:

```
Ingestion → Streaming (T+0:15 to T+4:45)
  S3-Landing-Zone → Ingestion-Service: Green data flow (4.2GB)
  Ingestion-Service → Kafka-Topic-Raw-Txns: Blue stream flow
  Data particles: 347,829 individual points moving along path

Streaming → Processing (T+5:00 to T+14:45)
  Kafka-Topic-Raw-Txns → Spark-Job-Transform-8847: Orange flow (high volume)
  Spark-Job-Transform-8847 → Validation-Service: Orange flow (processing complete)

Validation Split (T+14:45)
  Validation-Service → Valid-Records-342105: Green flow (98.35% of particles)
  Validation-Service → Invalid-Records-5724: Red flow (1.65% of particles)
  Split point visible as branching path at Validation-Service gate

Loading → Production (T+18:30 to T+27:15)
  Valid-Records-342105 → Redshift-Staging-Table: Purple flow
  Redshift-Staging-Table → Redshift-Production-Table: Purple flow (merge operation)
  Redshift-Production-Table → Looker-Dashboard: Green "data available" signal

Monitoring → Alert (T+15:30 to T+17:00)
  Validation-Service → CloudWatch-Metrics: Yellow metric stream
  CloudWatch-Metrics → PagerDuty-Alert-5848: Red alert line
  PagerDuty-Alert-5848 → Sarah Park: Pulsing red notification

Retry Path (T+20:00 to T+29:30)
  S3-Quarantine-Zone → Spark-Job-Transform-8848: Orange retry flow
  Retry path runs parallel to main path
  Recovered-Records-4891: Orange → Green (success)
  Failed-Final-Records-833: Red → Dark Red (permanent failure)

Communication (T+31:00)
  Sarah Park → Analytics-Team: White info line (Slack notification)
```

Line thickness indicates data volume. Color indicates state. Animation shows movement.

### Observed → Overlays

Observations become visual overlays:

```
Data Volume → Counters and flow intensity
  Raw-Records: "347,829" label, dense particle cluster
  Valid-Records: "342,105" label (98.35% indicator)
  Invalid-Records: "5,724" label (1.65% indicator)
  Recovered-Records: "4,891" label (85.4% recovery)
  Failed-Final: "833" label (0.24% final failure)

Processing Metrics → Real-time graphs
  Spark-Job-Transform-8847: Executor utilization graph (20 executors)
  Redshift write rate: "65,163 rows/min" indicator
  Validation throughput: Records processed per second

State Transitions → Color shifts
  T+14:45: 347,829 particles split into green (342,105) and red (5,724)
  T+26:00: 5,724 orange particles split into green (4,891) and dark red (833)

Timestamps → Floating time markers
  Each major step gets timestamp label
  SLA deadline shows countdown: "2h30m remaining" at T+27:30

Constraint Status → Badge overlays
  Quality threshold: "1.65% > 1.5%" red badge at Validation-Service
  SLA status: "2h30m buffer" green badge at Production-Table
  Encryption: "AES-256" green checkmark on storage volumes

Human Actions → Action indicators
  T+17:00: "Acknowledged" badge on Sarah Park
  T+20:00: "Retry Triggered" action marker on Sarah Park
  T+31:00: "Analysis Shared" action marker on Sarah Park

Resource Usage → Utilization overlays
  Spark cluster: "20/50 executors" gauge
  Redshift: "65K/100K rows/min" gauge
```

Observations change appearance and provide metrics, not interpretation.

### Constraints → Affordances and Limits

Constraints become visible restrictions and gates:

```
SLA Deadline (09:00 EST)
  Red vertical line at timeline position T+180min
  Progress indicator shows: "T+27:30 (152.5min before deadline)"
  Line turns green when data available (satisfied)

Quality Threshold (1.5% failure rate)
  Horizontal threshold line on validation metrics graph
  Graph line exceeds threshold: 1.65% observed
  Threshold breach triggers alert visualization

Schema Validation (required fields)
  Gate at Validation-Service
  Records without required fields cannot pass
  Visual: 5,724 particles bounce off gate into quarantine path
  Second validation: 833 particles permanently rejected

Resource Limits
  Spark executor cap: Gauge showing "20/50" (satisfied)
  Redshift write rate: Gauge showing "65K/100K" (satisfied)

Processing Window (3 hours)
  Timeline window from T+0 to T+180
  Actual duration: 29m30s (green indicator, well within window)

Retry Policy (1 retry max)
  Retry counter on Invalid-Records: "1/1 retries used"
  Failed-Final-Records show "0/1 retries remaining" (exhausted)

Security Constraint (encryption)
  Lock icons on S3-Landing-Zone, S3-Quarantine-Zone, Redshift
  Green checkmarks indicate encryption active

Data Freshness (< 6 hours)
  Age indicator on Raw-Records: "3.2 hours old" (green, satisfied)
```

Constraints shown as gates, limits, thresholds, and policy indicators.

### Time → The Moving Dimension

Time controls everything:

```
T=0:00 (06:00:00)
  - Airflow trigger appears
  - Scheduled-Batch-Window scope illuminates
  - SLA deadline marker appears at T+180min

T=0:15 (06:00:15)
  - Raw-Records-347829 materializes in S3-Landing-Zone
  - 347,829 particles appear as cluster
  - Data flow path from external source visible

T=1:30 to T=4:45 (06:01:30 to 06:04:45)
  - Particles flow from S3 → Ingestion-Service → Kafka
  - Stream animation shows progressive movement

T=5:00 (06:05:00)
  - Spark-Job-Transform-8847 activates (20 cubes appear)
  - Kafka → Spark path activates (orange)

T=14:45 (06:14:45)
  - Critical moment: particles reach Validation-Service gate
  - Split occurs: 98.35% flow green (pass), 1.65% flow red (fail)
  - Fork in path becomes visible

T=15:45 (06:15:45)
  - Alert path activates (red)
  - PagerDuty → Sarah Park line pulses

T=20:00 (06:20:00)
  - Retry path branches from quarantine (parallel path)
  - Second Spark job activates (10 cubes)
  - Retry particles begin movement

T=26:00 (06:26:00)
  - Second split: retry particles divide
  - 85.4% shift orange → green (recovered)
  - 14.6% shift red → dark red (permanent failure)

T=27:30 (06:27:30)
  - Production table updates
  - SLA deadline line turns green (satisfied, 2h30m early)
  - Dashboard refresh signal activates

T=29:30 (06:29:30)
  - Final state achieved
  - 346,996 particles in production (green, solid)
  - 833 particles in permanent quarantine (dark red)
  - All paths become historical (gray)

T=195:00 (09:15:00)
  - Alex Chen queries production table
  - Query visualization shows scan across 346,996 rows
```

Scrubbing time backward shows particles "unmerging" from production, validation "unsplitting", data flowing backward through pipeline.

Freezing at T=14:45 shows the critical validation split moment.

---

## Part 3: Multiple Views of Same Facts

### View 1: Data Engineer (Sarah Park) Perspective

**Emphasis:**
- Validation-Service metrics and split
- CloudWatch-Metrics and alert trigger
- Quarantine zone and retry path
- Quality threshold breach
- Spark job resource allocation
- Processing timings

**De-emphasis:**
- End-user analytics consumption (Looker)
- Individual record content
- Business meaning of data
- Analyst workflows

**Focus:**
Pipeline health? Quality issues? What failed and why? Should I retry?

**Distance:**
Medium - zoomed in on validation gate, quarantine zone, and retry mechanism

**Key Observations:**
- 1.65% failure rate (exceeded 1.5% threshold by 0.15%)
- 5,724 records failed initial validation
- Retry recovered 85.4% (4,891 records)
- 833 records permanently failed (0.24% of original batch)
- Pipeline completed 2h30m before SLA deadline
- All resource constraints satisfied

### View 2: Data Analyst (Alex Chen) Perspective

**Emphasis:**
- Redshift-Production-Table data availability
- SLA deadline status
- Data completeness (records available)
- Looker-Dashboard refresh
- Query execution timing

**De-emphasis:**
- Internal pipeline stages (Kafka, Spark details)
- Validation split mechanics
- Quarantine and retry paths
- Infrastructure resource usage
- Alert mechanisms

**Focus:**
Is data ready? Can I query it? How complete is it? Am I seeing today's data?

**Distance:**
Far - seeing only final state (production table) and availability signal

**Key Observations:**
- Data available at 06:27:30 (2h32m before 9am deadline)
- 346,996 records in production table
- Query completed successfully at 09:17:00
- New data visible in dashboard at 06:28:00
- 99.76% completeness (analyst may not care about 0.24% missing)

### View 3: Platform Team Perspective

**Emphasis:**
- Resource utilization (Spark executors, Redshift write rate)
- Infrastructure layer scopes (S3, Kafka, Spark, Redshift)
- Processing durations and throughput
- Security constraints (encryption verification)
- System capacity vs. usage

**De-emphasis:**
- Business logic and validation rules
- Individual record failures
- End-user analytics consumption
- Organizational communication

**Focus:**
Infrastructure performing? Resource limits adequate? Security compliant? Costs reasonable?

**Distance:**
Medium - infrastructure layer emphasized, data content de-emphasized

**Key Observations:**
- Spark: 20/50 executors used (60% headroom)
- Redshift: 65K/100K rows/min (35% headroom)
- S3 writes: 4.2GB ingested in 4m30s
- All encryption constraints satisfied
- Total processing: 29m30s (well within 3-hour window)
- No infrastructure constraints violated

### View 4: Pipeline Orchestration Perspective

**Emphasis:**
- Complete timeline (all 29m30s)
- All path traversals (main + retry)
- Constraint satisfaction/violations across all types
- Parallel path execution
- State transitions at each stage
- End-to-end success rate

**De-emphasis:**
- Individual service internals
- Human decision-making
- Real-time urgency
- Infrastructure capacity details

**Focus:**
Full pipeline flow? Where are bottlenecks? Success rates? Which constraints matter?

**Distance:**
Far - seeing entire pipeline as single flow with branches

**Key Observations:**
- Total duration: 29m30s (main + retry)
- Processing stages: Ingest (4.7m) → Transform (9.8m) → Load (12.5m)
- Success rate: 99.76% (1 SLA satisfied, 1 quality threshold violated)
- Retry effectiveness: 85.4% recovery
- Parallel paths: Main completed at T+27:15, retry at T+29:30
- Bottleneck: Validation + Loading took 12m30s (42% of total time)

---

## Part 4: Reality Check

### Test 1: Point and Name

Point at any element and name its primitive:

| Point at | Answer | Primitive |
|----------|--------|-----------|
| Raw-Records-347829 | A batch of transaction records | Thing |
| Data-Processing-Zone | Technical scope for transformation | Scope |
| Flow from Kafka to Spark | Data movement path | Path |
| "342,105 records" counter | Observation of validation pass count | Observed |
| Split at validation gate | Observation of validation outcomes | Observed |
| "1.5% threshold" line | Quality constraint | Constraint |
| Red badge "1.65% > 1.5%" | Observation of constraint violation | Observed + Constraint |
| Timeline scrubber | Time dimension | Time |
| Green glow on valid records | Observed quality-validated state | Scope (state-based) |
| "20/50 executors" gauge | Observation of resource constraint status | Observed + Constraint |

All answers are primitives. ✓

### Test 2: No New Concepts

Concepts NOT introduced:
- "Data quality culture"
- "Pipeline maturity"
- "Engineering excellence"
- "System reliability"
- "ETL best practices"
- "Data governance framework"

Only facts:
- Records moved through pipeline
- Validation split records by schema compliance
- Some records failed validation
- Retry recovered most failures
- Pipeline completed before deadline
- Constraints satisfied or violated

✓

### Test 3: Multiple Roles See Same Facts

Data engineer sees: 347,829 records entered, 346,996 reached production (99.76%)
Data analyst sees: 347,829 records entered, 346,996 reached production (99.76%)
Platform team sees: 347,829 records entered, 346,996 reached production (99.76%)
Orchestration view sees: 347,829 records entered, 346,996 reached production (99.76%)

They emphasize different aspects (quality vs. availability vs. infrastructure vs. flow), but the facts are identical. ✓

### Test 4: Causality Not Implied

What we DO NOT say:
- "Missing fields caused validation failure"
- "Retry mechanism fixed the records"
- "Sarah's quick response prevented SLA breach"
- "Good architecture enabled high success rate"

What we DO say:
- "5,724 records lacked required fields, observed at T+14:45"
- "Retry executed at T+20:00, 4,891 records passed validation at T+26:00"
- "SLA deadline: 09:00, data available: 06:27:30 (observed 2h32m buffer)"
- "Final state: 346,996 records in production, 833 in permanent quarantine"

We show temporal sequence, split points, and outcomes. We do not assert causation.

The retry correlated with recovery of 4,891 records, but we don't claim the retry "caused" them to become valid - they may have been valid in a different processing context, or the retry job handled edge cases better, or external reference data became available. Not observed, not claimed. ✓

### Test 5: Can Traverse

Starting at S3-Landing-Zone at T=0:15, can we follow paths?

**Main path:**
1. S3-Landing-Zone → Ingestion-Service (read)
2. Ingestion-Service → Kafka-Topic-Raw-Txns (publish)
3. Kafka-Topic-Raw-Txns → Spark-Job-Transform-8847 (consume)
4. Spark-Job-Transform-8847 → Validation-Service (validate)
5. Validation-Service → Valid-Records-342105 (pass)
6. Valid-Records-342105 → Redshift-Staging-Table (load)
7. Redshift-Staging-Table → Redshift-Production-Table (merge)
8. Redshift-Production-Table → Looker-Dashboard (refresh)

**Failure path:**
4. Validation-Service → Invalid-Records-5724 (fail)
5. Invalid-Records-5724 → S3-Quarantine-Zone (quarantine)

**Retry path:**
6. S3-Quarantine-Zone → Spark-Job-Transform-8848 (retry)
7. Spark-Job-Transform-8848 → Validation-Service (re-validate)
8. Validation-Service → Recovered-Records-4891 (pass on retry)
9. Recovered-Records-4891 → Redshift-Staging-Table (load)
10. Redshift-Staging-Table → Redshift-Production-Table (merge incremental)

**Permanent failure path:**
8. Validation-Service → Failed-Final-Records-833 (fail again)
9. Failed-Final-Records-833 → S3-Quarantine-Zone/permanent (final quarantine)

Every step is observable. Every path has data moving along it. Split and merge points are explicit. ✓

---

## Part 5: What This Example Demonstrates

### It Shows

1. **Data as thing moving through space**
   - 347,829 records as observable entity
   - State changes: raw → transformed → validated → loaded
   - Particles split and recombine based on validation

2. **Quality constraints as gates**
   - Validation-Service acts as gate
   - Records passing: green path
   - Records failing: red path to quarantine
   - Binary outcome observable

3. **Partial success explicitly**
   - 98.35% pass rate (342,105 records)
   - 1.65% failure rate (5,724 records)
   - Not "success" or "failure" - both/and

4. **Retry mechanics observable**
   - Failed records queued
   - Retry path branches from quarantine
   - Second validation with different outcome
   - Recovery: 85.4%, permanent failure: 14.6%

5. **Multiple constraint types simultaneously**
   - Time: SLA deadline (satisfied)
   - Quality: failure rate threshold (violated)
   - Resource: executor limit (satisfied)
   - Security: encryption (satisfied)
   - Policy: retry max (satisfied)

6. **Parallel path execution**
   - Main path continues while retry runs
   - Both paths merge into production table
   - Timing independent, outcome aggregated

### It Does Not Show

1. **Why records failed validation**
   - Missing fields observed, but why missing?
   - Were they incomplete at source? Processing bug? Schema change?
   - Not observed, not shown

2. **Why retry recovered 85.4%**
   - Same validation rules applied
   - Did records change? Did reference data arrive? Different code path?
   - Correlation visible, causation unknown

3. **Whether 99.76% success is "good"**
   - Is 833 failed records acceptable?
   - Business impact of missing 0.24%?
   - Judgment external to framework

4. **Whether Sarah's actions were optimal**
   - Retry triggered at T+20:00
   - Could it have been earlier? Later? Automated?
   - Performance evaluation external

5. **Business meaning of data**
   - Transaction records - but for what?
   - Revenue? Orders? Events?
   - Content not visualized, only flow

6. **Root cause of quality threshold breach**
   - 1.65% exceeded 1.5% threshold
   - Is this a trend? Anomaly? Systemic issue?
   - Requires historical analysis not shown

---

## Part 6: Implementation Notes

### Data Structure (Conceptual)

```json
{
  "things": [
    {
      "id": "raw-records-347829",
      "type": "dataset",
      "record_count": 347829,
      "size_bytes": 4503599627,
      "arrived": "2024-12-10T06:00:15Z"
    },
    {
      "id": "valid-records-342105",
      "type": "dataset",
      "record_count": 342105,
      "parent": "raw-records-347829",
      "validation_state": "passed"
    },
    {
      "id": "invalid-records-5724",
      "type": "dataset",
      "record_count": 5724,
      "parent": "raw-records-347829",
      "validation_state": "failed",
      "failure_reason": "missing_required_fields"
    },
    {
      "id": "spark-job-transform-8847",
      "type": "compute-job",
      "executors": 20,
      "started": "2024-12-10T06:05:00Z",
      "completed": "2024-12-10T06:14:45Z"
    }
    // ... more things
  ],
  "scopes": [
    {
      "id": "data-landing-zone",
      "type": "technical-zone"
    },
    {
      "id": "quality-validated-state",
      "type": "data-state",
      "criteria": "all_required_fields_present"
    },
    {
      "id": "sla-deadline-0900",
      "type": "temporal-constraint",
      "deadline": "2024-12-10T09:00:00Z"
    }
    // ... more scopes
  ],
  "paths": [
    {
      "id": "ingestion-to-streaming",
      "from": "s3-landing-zone",
      "to": "kafka-topic-raw-txns",
      "via": "ingestion-service",
      "thing_moved": "raw-records-347829",
      "started": "2024-12-10T06:01:30Z",
      "completed": "2024-12-10T06:04:45Z",
      "duration_seconds": 195
    },
    {
      "id": "validation-split-pass",
      "from": "validation-service",
      "to": "transformed-records-342105",
      "thing_moved": "valid-records-342105",
      "observed": "2024-12-10T06:14:45Z",
      "split_ratio": 0.9835
    },
    {
      "id": "validation-split-fail",
      "from": "validation-service",
      "to": "s3-quarantine-zone",
      "thing_moved": "invalid-records-5724",
      "observed": "2024-12-10T06:14:45Z",
      "split_ratio": 0.0165
    }
    // ... more paths, including retry paths
  ],
  "observations": [
    {
      "timestamp": "2024-12-10T06:00:15Z",
      "thing": "raw-records-347829",
      "event": "arrived",
      "location": "s3-landing-zone",
      "properties": {
        "record_count": 347829,
        "size_gb": 4.2
      }
    },
    {
      "timestamp": "2024-12-10T06:14:45Z",
      "thing": "validation-service",
      "event": "validation_complete",
      "results": {
        "passed": 342105,
        "failed": 5724,
        "pass_rate": 0.9835,
        "failure_rate": 0.0165
      }
    },
    {
      "timestamp": "2024-12-10T06:27:30Z",
      "thing": "redshift-production-table",
      "event": "data_available",
      "record_count": 342105
    }
    // ... more observations (40+ total)
  ],
  "constraints": [
    {
      "id": "sla-deadline",
      "type": "time-deadline",
      "applies_to": "redshift-production-table",
      "threshold": "2024-12-10T09:00:00Z",
      "observed_completion": "2024-12-10T06:27:30Z",
      "buffer_seconds": 9150,
      "satisfied": true
    },
    {
      "id": "quality-failure-rate",
      "type": "quality-threshold",
      "applies_to": "validation-service",
      "metric": "failure_rate",
      "threshold": 0.015,
      "observed": 0.0165,
      "satisfied": false,
      "triggered_alert": "pagerduty-alert-5848"
    },
    {
      "id": "schema-validation",
      "type": "data-quality",
      "applies_to": "validation-service",
      "required_fields": ["customer_id", "transaction_id", "amount", "timestamp", "currency"],
      "failures": [
        {"record_count": 5724, "attempt": 1},
        {"record_count": 833, "attempt": 2}
      ]
    }
    // ... more constraints
  ]
}
```

### Projection Parameters

```yaml
view_config_data_engineer:
  camera_position: [0, 6, 12]
  focus: ["validation-service", "s3-quarantine-zone", "cloudwatch-metrics"]
  time_range: ["2024-12-10T06:00:00Z", "2024-12-10T06:35:00Z"]
  visible_scopes:
    - "data-processing-zone"
    - "spark-compute-layer"
    - "quality-validated-state"
    - "quality-failed-state"
  visible_things:
    include: ["validation-service", "valid-records-342105", "invalid-records-5724",
              "spark-job-transform-8847", "spark-job-transform-8848",
              "s3-quarantine-zone", "cloudwatch-metrics", "sarah-park"]
  emphasis:
    - type: "validation-split"
      intensity: 1.0
    - type: "constraint-violations"
      intensity: 0.9
    - type: "retry-paths"
      intensity: 0.8
  particle_visualization:
    show_individual_records: true
    split_animation: true
    color_by_state: true

view_config_data_analyst:
  camera_position: [15, 10, 20]
  focus: ["redshift-production-table", "looker-dashboard-daily-revenue"]
  time_range: ["2024-12-10T06:00:00Z", "2024-12-10T09:30:00Z"]
  visible_scopes:
    - "data-storage-zone"
    - "data-serving-zone"
    - "sla-deadline-0900"
  visible_things:
    include: ["redshift-production-table", "looker-dashboard-daily-revenue",
              "alex-chen"]
    exclude: ["kafka-topic-raw-txns", "spark-job-transform-8847",
              "s3-quarantine-zone", "validation-service"]
  emphasis:
    - type: "data-availability"
      intensity: 1.0
    - type: "sla-status"
      intensity: 0.9
  deemphasis:
    - type: "internal-pipeline-stages"
      intensity: 0.1
  particle_visualization:
    show_individual_records: false
    aggregate_view: true
    show_only_final_state: true

view_config_platform_team:
  camera_position: [0, 15, 25]
  focus: ["spark-compute-layer", "redshift-warehouse-layer"]
  time_range: ["2024-12-10T06:00:00Z", "2024-12-10T06:35:00Z"]
  visible_scopes:
    - "aws-us-east-1"
    - "s3-storage-layer"
    - "kafka-streaming-layer"
    - "spark-compute-layer"
    - "redshift-warehouse-layer"
  visible_things: "all"
  emphasis:
    - type: "resource-utilization"
      intensity: 1.0
    - type: "infrastructure-constraints"
      intensity: 0.9
    - type: "throughput-metrics"
      intensity: 0.8
  deemphasis:
    - type: "business-logic"
      intensity: 0.2
    - type: "individual-records"
      intensity: 0.1
  show_resource_gauges: true
  show_cost_estimates: false

view_config_full_pipeline:
  camera_position: [0, 20, 40]
  focus: null  # entire pipeline
  time_range: ["2024-12-10T06:00:00Z", "2024-12-10T09:30:00Z"]
  visible_scopes: "all"
  visible_things: "all"
  time_scrubber_visible: true
  emphasis:
    - type: "end-to-end-flow"
      intensity: 1.0
    - type: "parallel-paths"
      intensity: 0.9
    - type: "constraint-satisfaction"
      intensity: 0.8
  particle_visualization:
    show_flow_animation: true
    show_split_points: true
    show_merge_points: true
    color_by_state: true
  annotations:
    show_stage_durations: true
    show_success_rates: true
    show_bottlenecks: true
```

---

## Conclusion

This example demonstrates data pipeline traversal as observable movement through technical scopes using only the six primitives.

**Key demonstrations:**

1. **Data as observable thing**: 347,829 records as concrete entity moving through stages
2. **Quality gates as constraints**: Validation splits data based on observable schema compliance
3. **Partial success**: 98.35% success, 1.65% failure - both outcomes visible simultaneously
4. **Retry mechanics**: Failed records take alternate path, 85.4% recover, 14.6% permanently fail
5. **Multiple constraint types**: Time (SLA), quality (threshold), resource (limits), security (encryption), policy (retry max)
6. **Four perspectives**: Engineer (quality focus), analyst (availability focus), platform (infrastructure focus), orchestration (flow focus)

**Maintains discipline:**

- No interpretation of why records failed (schema non-compliance observed, cause unknown)
- No judgment of success rate (99.76% is factual, "good enough" is external)
- No causation claims (retry correlated with recovery, causation not asserted)
- No concepts beyond six primitives
- Every element passes point-and-name test
- Partial success explicitly shown (not binary success/failure)

This is data pipeline operation projected as factual traversal with observable splits, merges, and outcomes - not explained as technical narrative or quality assessment.