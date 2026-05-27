# Example 06: Hybrid Environment Traversal

A fictional organization operating a datacenter, an Azure tenant, and an AWS tenant, with one application traversal crossing all three environments.

## The Scenario

Dispatch planner Priya Nair opens shipment `SH-44192` in the unified operations application. The request starts in Azure, retrieves the authoritative shipment record from the datacenter, retrieves live telemetry summary from AWS, and returns one combined view.

This example demonstrates:
- One factual traversal crossing on-prem, Azure, and AWS
- Applications distributed across all three environments
- Cross-environment constraints without new abstractions
- Time-ordered observations over a short hybrid request
- One description supporting multiple infrastructure views

---

## Part 1: Factual Description

### Things That Exist

All Things listed below are concrete instances.

```text
Priya Nair                 # Class: instance, Type: person, Identity: employee_id
SH-44192                   # Class: instance, Type: shipment_record, Identity: shipment_id
Entra-ID                   # Class: instance, Type: identity_service, Identity: service_name
OpsPortal-Web              # Class: instance, Type: application, Identity: service_name
APIManagement-OPS          # Class: instance, Type: api_gateway, Identity: service_name
AKS-IntegrationHub         # Class: instance, Type: application_runtime, Identity: service_name
TMS-Core                   # Class: instance, Type: application, Identity: service_name
SQL-TMS-01                 # Class: instance, Type: database, Identity: db_name
Telemetry-API              # Class: instance, Type: application, Identity: service_name
Aurora-Fleet               # Class: instance, Type: database, Identity: db_name
```

### Scopes Where Things Exist

```text
Corporate Operations       # Organizational scope
Datacenter Scope           # Physical infrastructure scope
Azure Tenant Scope         # Cloud scope
AWS Tenant Scope           # Cloud scope
Private WAN                # Connectivity scope
Identity Scope             # Authentication scope
Production                 # Operational scope
Business Hours             # Temporal scope (Mon-Fri 09:00-17:00 UTC)
```

Membership facts:

```text
Priya Nair exists within Corporate Operations
Priya Nair exists within Business Hours
SH-44192 exists within Production
Entra-ID exists within Identity Scope
OpsPortal-Web exists within Azure Tenant Scope
APIManagement-OPS exists within Azure Tenant Scope
AKS-IntegrationHub exists within Azure Tenant Scope
TMS-Core exists within Datacenter Scope
SQL-TMS-01 exists within Datacenter Scope
Telemetry-API exists within AWS Tenant Scope
Aurora-Fleet exists within AWS Tenant Scope
```

### Paths That Connect Things

```text
Path 1: User access
  Priya Nair moves request for SH-44192 to OpsPortal-Web
  Authentication token moves from Entra-ID to OpsPortal-Web
  Shipment record moves from SH-44192 to OpsPortal-Web

Path 2: Datacenter record retrieval
  Shipment query moves from OpsPortal-Web to APIManagement-OPS
  Shipment query moves from APIManagement-OPS to AKS-IntegrationHub
  Shipment query moves from AKS-IntegrationHub to TMS-Core
  Shipment record moves from SQL-TMS-01 to TMS-Core
  Shipment record moves from TMS-Core to AKS-IntegrationHub

Path 3: AWS telemetry retrieval
  Telemetry query moves from AKS-IntegrationHub to Telemetry-API
  Telemetry summary moves from Aurora-Fleet to Telemetry-API
  Telemetry summary moves from Telemetry-API to AKS-IntegrationHub

Path 4: Unified response
  Combined shipment view moves from AKS-IntegrationHub to OpsPortal-Web
  Combined shipment view moves from OpsPortal-Web to Priya Nair
```

### Observations Made

```text
2026-04-20T13:14:02Z - Entra-ID delivered authentication token to OpsPortal-Web
2026-04-20T13:14:03Z - Priya Nair opened SH-44192 in OpsPortal-Web
2026-04-20T13:14:03Z - OpsPortal-Web loaded SH-44192 as active shipment record
2026-04-20T13:14:03Z - OpsPortal-Web sent shipment query to APIManagement-OPS
2026-04-20T13:14:03Z - APIManagement-OPS routed shipment query to AKS-IntegrationHub
2026-04-20T13:14:04Z - AKS-IntegrationHub requested shipment record from TMS-Core
2026-04-20T13:14:04Z - TMS-Core read SH-44192 from SQL-TMS-01
2026-04-20T13:14:04Z - TMS-Core returned shipment record to AKS-IntegrationHub
2026-04-20T13:14:05Z - AKS-IntegrationHub requested telemetry summary from Telemetry-API
2026-04-20T13:14:05Z - Telemetry-API read latest telemetry summary from Aurora-Fleet
2026-04-20T13:14:05Z - Telemetry-API returned telemetry summary to AKS-IntegrationHub
2026-04-20T13:14:06Z - AKS-IntegrationHub assembled combined shipment view
2026-04-20T13:14:06Z - OpsPortal-Web rendered combined shipment view to Priya Nair
```

### Constraints That Apply

```text
Constraint 1: OpsPortal-Web access requires Entra-ID authentication
  Type: Policy
  Scope: Identity Scope

Constraint 2: TMS-Core is authoritative for shipment master data
  Type: Structural
  Scope: Datacenter Scope

Constraint 3: Telemetry-API provides read-only telemetry summary to AKS-IntegrationHub
  Type: Policy
  Scope: AWS Tenant Scope

Constraint 4: Datacenter shipment traffic moves only across Private WAN links
  Type: Structural
  Scope: Private WAN

Constraint 5: AWS telemetry traffic moves only across Private WAN links
  Type: Structural
  Scope: Private WAN

Constraint 6: Unified shipment view expected within 5 seconds from open to render
  Type: Observed
  Scope: Production
  Observed: 3 seconds elapsed from open to render

Constraint 7: Production shipment access occurs only during Business Hours
  Type: Policy
  Scope: Business Hours
  Rule: Mon-Fri 09:00-17:00 UTC
  Observed: Satisfied at 2026-04-20T13:14:03Z
```

### Time Ordering

```text
Timeline:
  T+0s  13:14:02 - Authentication token delivered
  T+1s  13:14:03 - Shipment view request opened and shipment record loaded in Azure
  T+2s  13:14:04 - Datacenter shipment record retrieved
  T+3s  13:14:05 - AWS telemetry summary retrieved
  T+4s  13:14:06 - Combined view assembled and rendered

Total elapsed: 4 seconds
```

---

## Part 2: Spatial Projection Mapping

### Things → Objects in Space

```text
Priya Nair           → Person object
SH-44192             → Shipment object
Entra-ID             → Identity service object
OpsPortal-Web        → Application object in Azure plane
APIManagement-OPS    → API gateway object in Azure plane
AKS-IntegrationHub   → Integration runtime object in Azure plane
TMS-Core             → Application object in datacenter plane
Telemetry-API        → Application object in AWS plane
SQL-TMS-01           → Database object in datacenter plane
Aurora-Fleet         → Database object in AWS plane
```

Visual form indicates existence only.

### Scopes → Spatial Grouping

```text
Datacenter Scope     → Left-side physical plane
Azure Tenant Scope   → Center cloud plane
AWS Tenant Scope     → Right-side cloud plane
Private WAN          → Routed corridor linking all three planes
Identity Scope       → Overlay band on Azure entry path
Production           → Shared base layer
Business Hours       → Lit temporal state
```

Objects can be seen across multiple scopes without duplication.

### Paths → Routed Connections

```text
Entra-ID → OpsPortal-Web
Priya Nair → OpsPortal-Web
SH-44192 → OpsPortal-Web
OpsPortal-Web → APIManagement-OPS → AKS-IntegrationHub
AKS-IntegrationHub → TMS-Core → SQL-TMS-01 → TMS-Core → AKS-IntegrationHub
AKS-IntegrationHub → Telemetry-API → Aurora-Fleet → Telemetry-API → AKS-IntegrationHub
AKS-IntegrationHub → OpsPortal-Web → Priya Nair
```

Every line represents observed movement of a request, record, or response.

### Observed → Overlays

```text
Authentication         → Marker at Azure entry path
Datacenter read        → Pulse on TMS-Core and SQL-TMS-01
AWS telemetry read     → Pulse on Telemetry-API and Aurora-Fleet
Unified render         → Highlight on OpsPortal-Web and Priya Nair
```

Timestamps appear at each observed step.

### Constraints → Affordances and Limits

```text
Entra-ID requirement         → Entry path blocked until authentication observed
Authoritative datacenter     → Shipment master path emphasized toward TMS-Core
Read-only telemetry          → AWS path shown as query-and-return only
Private WAN only             → Cross-environment lines restricted to one corridor
5-second expectation         → Time indicator on end-to-end request path
```

Constraints restrict traversal, not existence.

### Time → Ordered Reveal

```text
Step 1: Authentication
Step 2: Azure request
Step 3: Datacenter retrieval
Step 4: AWS retrieval
Step 5: Unified render
```

Time controls path activation and observation overlays.

---

## Part 3: Reality Check

- Every object named in projection maps to one of the six primitives.
- The same description supports infrastructure, application, and operations views.
- No visual layer explains architecture intent.
- No path implies causality beyond observed movement.
