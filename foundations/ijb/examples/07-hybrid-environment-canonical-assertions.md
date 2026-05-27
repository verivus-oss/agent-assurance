# Example 07: Hybrid Environment Canonical Assertions

A canonical assertion version of the hybrid datacenter, Azure, and AWS traversal, using one parseable substrate for structure, instances, observations, constraints, and replay.

## The Scenario

Dispatch planner Priya Nair opens shipment `SH-44192` in the unified operations application. The request starts in Azure, retrieves shipment master data from the datacenter, retrieves telemetry summary from AWS, and returns one combined view.

Scope note:
- This canonical version includes the shipment subject and the observed-path participants only.
- It omits inventory elements from Example 06 that do not participate in the recorded traversal.

This example demonstrates:
- Canonical assertion grammar for a hybrid estate
- One traversal crossing datacenter, Azure, and AWS
- Structural vs instance separation
- Explicit observation records over prior assertions
- Constraint checking over cross-environment movement
- Replay and projection from the same assertion set

---

## Part 1: Canonical Assertions

### Structural declarations

```text
A-scope-corp-ops = scope(id=Corporate-Operations,class=structural,type=org)
A-scope-datacenter = scope(id=Datacenter-Scope,class=structural,type=infra)
A-scope-azure = scope(id=Azure-Tenant-Scope,class=structural,type=cloud)
A-scope-aws = scope(id=AWS-Tenant-Scope,class=structural,type=cloud)
A-scope-private-wan = scope(id=Private-WAN,class=structural,type=network)
A-scope-identity = scope(id=Identity-Scope,class=structural,type=identity)
A-scope-production = scope(id=Production,class=structural,type=ops)
A-scope-business-hours = scope(id=Business-Hours,class=structural,type=time_window)

A-thing-planner = thing(id=Dispatch-Planner,class=structural,type=person,identity=employee_id)
A-thing-shipment = thing(id=Shipment,class=structural,type=shipment_record,identity=shipment_id)
A-thing-opsportal = thing(id=OpsPortal-Web,class=structural,type=application,identity=service_name)
A-thing-apimgmt = thing(id=APIManagement-OPS,class=structural,type=api_gateway,identity=service_name)
A-thing-integrationhub = thing(id=AKS-IntegrationHub,class=structural,type=application_runtime,identity=service_name)
A-thing-tmscore = thing(id=TMS-Core,class=structural,type=application,identity=service_name)
A-thing-sqltms = thing(id=SQL-TMS,class=structural,type=database,identity=db_name)
A-thing-telemetryapi = thing(id=Telemetry-API,class=structural,type=application,identity=service_name)
A-thing-aurora = thing(id=Aurora-Fleet,class=structural,type=database,identity=db_name)
A-thing-entra = thing(id=Entra-ID,class=structural,type=identity_service,identity=service_name)

A-path-auth-token = path(id=auth_token_delivery,class=structural,from=Entra-ID,to=OpsPortal-Web,within=Identity-Scope,moves=auth_token)
A-path-user-open = path(id=user_open_shipment,class=structural,from=Dispatch-Planner,to=OpsPortal-Web,within=Azure-Tenant-Scope,moves=shipment_request)
A-path-open-shipment = path(id=open_shipment_record,class=structural,from=OpsPortal-Web,to=Shipment,within=Azure-Tenant-Scope,moves=shipment_record)
A-path-query-gateway = path(id=query_gateway,class=structural,from=OpsPortal-Web,to=APIManagement-OPS,within=Azure-Tenant-Scope,moves=shipment_query)
A-path-query-integration = path(id=query_integration,class=structural,from=APIManagement-OPS,to=AKS-IntegrationHub,within=Azure-Tenant-Scope,moves=shipment_query)
A-path-query-tms = path(id=query_tms,class=structural,from=AKS-IntegrationHub,to=TMS-Core,within=Private-WAN,moves=shipment_query)
A-path-read-sql = path(id=read_shipment_record,class=structural,from=SQL-TMS,to=TMS-Core,within=Datacenter-Scope,moves=shipment_record)
A-path-return-sql = path(id=return_shipment_record,class=structural,from=TMS-Core,to=AKS-IntegrationHub,within=Private-WAN,moves=shipment_record)
A-path-query-telemetry = path(id=query_telemetry,class=structural,from=AKS-IntegrationHub,to=Telemetry-API,within=Private-WAN,moves=telemetry_query)
A-path-read-telemetry = path(id=read_telemetry_summary,class=structural,from=Aurora-Fleet,to=Telemetry-API,within=AWS-Tenant-Scope,moves=telemetry_summary)
A-path-return-telemetry = path(id=return_telemetry_summary,class=structural,from=Telemetry-API,to=AKS-IntegrationHub,within=Private-WAN,moves=telemetry_summary)
A-path-return-view = path(id=return_unified_view,class=structural,from=AKS-IntegrationHub,to=OpsPortal-Web,within=Azure-Tenant-Scope,moves=combined_view)
A-path-render-user = path(id=render_unified_view,class=structural,from=OpsPortal-Web,to=Dispatch-Planner,within=Azure-Tenant-Scope,moves=combined_view)

A-constraint-auth-required = constraint(id=auth_required,type=policy,target=user_open_shipment,within=Identity-Scope,rule="OpsPortal-Web access requires Entra-ID authentication")
A-constraint-tms-authoritative = constraint(id=tms_authoritative,type=structural,target=read_shipment_record,within=Datacenter-Scope,rule="shipment master data is authoritative in TMS-Core and SQL-TMS")
A-constraint-telemetry-readonly = constraint(id=telemetry_readonly,type=policy,target=return_telemetry_summary,within=AWS-Tenant-Scope,rule="Telemetry-API provides read-only telemetry summary")
A-constraint-private-wan-tms-query = constraint(id=private_wan_only_tms_query,type=structural,target=query_tms,within=Private-WAN,rule="TMS shipment query traffic moves only across Private-WAN")
A-constraint-private-wan-tms-return = constraint(id=private_wan_only_tms_return,type=structural,target=return_shipment_record,within=Private-WAN,rule="TMS shipment return traffic moves only across Private-WAN")
A-constraint-private-wan-telemetry-query = constraint(id=private_wan_only_telemetry_query,type=structural,target=query_telemetry,within=Private-WAN,rule="telemetry query traffic moves only across Private-WAN")
A-constraint-private-wan-telemetry-return = constraint(id=private_wan_only_telemetry_return,type=structural,target=return_telemetry_summary,within=Private-WAN,rule="telemetry return traffic moves only across Private-WAN")
A-constraint-response-slo = constraint(id=response_within_5s,type=observed,target=render_unified_view,within=Production,rule="render_unified_view must occur within 5 seconds of user_open_shipment")
A-constraint-business-hours = constraint(id=business_hours_access,type=policy,target=user_open_shipment,within=Business-Hours,rule="production shipment access occurs only during Business-Hours (Mon-Fri 09:00-17:00 UTC)")
```

### Instance declarations

```text
A-thing-priya = thing(id=Priya-Nair,class=instance,instance_of=Dispatch-Planner,type=person,identity=employee_id)
A-thing-sh44192 = thing(id=SH-44192,class=instance,instance_of=Shipment,type=shipment_record,identity=shipment_id)
A-thing-opsportal-01 = thing(id=OpsPortal-Web-01,class=instance,instance_of=OpsPortal-Web,type=application,identity=service_name)
A-thing-apimgmt-01 = thing(id=APIManagement-OPS-01,class=instance,instance_of=APIManagement-OPS,type=api_gateway,identity=service_name)
A-thing-integrationhub-01 = thing(id=AKS-IntegrationHub-01,class=instance,instance_of=AKS-IntegrationHub,type=application_runtime,identity=service_name)
A-thing-tmscore-01 = thing(id=TMS-Core-01,class=instance,instance_of=TMS-Core,type=application,identity=service_name)
A-thing-sqltms-01 = thing(id=SQL-TMS-01,class=instance,instance_of=SQL-TMS,type=database,identity=db_name)
A-thing-telemetryapi-01 = thing(id=Telemetry-API-01,class=instance,instance_of=Telemetry-API,type=application,identity=service_name)
A-thing-aurora-01 = thing(id=Aurora-Fleet-01,class=instance,instance_of=Aurora-Fleet,type=database,identity=db_name)
A-thing-entra-01 = thing(id=Entra-ID-01,class=instance,instance_of=Entra-ID,type=identity_service,identity=service_name)

A-scope-priya-corp = scope(thing=Priya-Nair,within=Corporate-Operations)
A-scope-priya-hours = scope(thing=Priya-Nair,within=Business-Hours)
A-scope-shipment-prod = scope(thing=SH-44192,within=Production)
A-scope-opsportal-azure = scope(thing=OpsPortal-Web-01,within=Azure-Tenant-Scope)
A-scope-apimgmt-azure = scope(thing=APIManagement-OPS-01,within=Azure-Tenant-Scope)
A-scope-integrationhub-azure = scope(thing=AKS-IntegrationHub-01,within=Azure-Tenant-Scope)
A-scope-tms-dc = scope(thing=TMS-Core-01,within=Datacenter-Scope)
A-scope-sql-dc = scope(thing=SQL-TMS-01,within=Datacenter-Scope)
A-scope-telemetry-aws = scope(thing=Telemetry-API-01,within=AWS-Tenant-Scope)
A-scope-aurora-aws = scope(thing=Aurora-Fleet-01,within=AWS-Tenant-Scope)
A-scope-entra-identity = scope(thing=Entra-ID-01,within=Identity-Scope)

A-path-auth-token-44192 = path(id=auth_token_delivery_44192,class=instance,instance_of=auth_token_delivery,from=Entra-ID-01,to=OpsPortal-Web-01,within=Identity-Scope,moves=auth_token)
A-path-user-open-44192 = path(id=user_open_shipment_44192,class=instance,instance_of=user_open_shipment,from=Priya-Nair,to=OpsPortal-Web-01,within=Azure-Tenant-Scope,moves=shipment_request)
A-path-open-shipment-44192 = path(id=open_shipment_record_44192,class=instance,instance_of=open_shipment_record,from=OpsPortal-Web-01,to=SH-44192,within=Azure-Tenant-Scope,moves=shipment_record)
A-path-query-gateway-44192 = path(id=query_gateway_44192,class=instance,instance_of=query_gateway,from=OpsPortal-Web-01,to=APIManagement-OPS-01,within=Azure-Tenant-Scope,moves=shipment_query)
A-path-query-integration-44192 = path(id=query_integration_44192,class=instance,instance_of=query_integration,from=APIManagement-OPS-01,to=AKS-IntegrationHub-01,within=Azure-Tenant-Scope,moves=shipment_query)
A-path-query-tms-44192 = path(id=query_tms_44192,class=instance,instance_of=query_tms,from=AKS-IntegrationHub-01,to=TMS-Core-01,within=Private-WAN,moves=shipment_query)
A-path-read-sql-44192 = path(id=read_shipment_record_44192,class=instance,instance_of=read_shipment_record,from=SQL-TMS-01,to=TMS-Core-01,within=Datacenter-Scope,moves=shipment_record)
A-path-return-sql-44192 = path(id=return_shipment_record_44192,class=instance,instance_of=return_shipment_record,from=TMS-Core-01,to=AKS-IntegrationHub-01,within=Private-WAN,moves=shipment_record)
A-path-query-telemetry-44192 = path(id=query_telemetry_44192,class=instance,instance_of=query_telemetry,from=AKS-IntegrationHub-01,to=Telemetry-API-01,within=Private-WAN,moves=telemetry_query)
A-path-read-telemetry-44192 = path(id=read_telemetry_summary_44192,class=instance,instance_of=read_telemetry_summary,from=Aurora-Fleet-01,to=Telemetry-API-01,within=AWS-Tenant-Scope,moves=telemetry_summary)
A-path-return-telemetry-44192 = path(id=return_telemetry_summary_44192,class=instance,instance_of=return_telemetry_summary,from=Telemetry-API-01,to=AKS-IntegrationHub-01,within=Private-WAN,moves=telemetry_summary)
A-path-return-view-44192 = path(id=return_unified_view_44192,class=instance,instance_of=return_unified_view,from=AKS-IntegrationHub-01,to=OpsPortal-Web-01,within=Azure-Tenant-Scope,moves=combined_view)
A-path-render-user-44192 = path(id=render_unified_view_44192,class=instance,instance_of=render_unified_view,from=OpsPortal-Web-01,to=Priya-Nair,within=Azure-Tenant-Scope,moves=combined_view)
```

### Time and observation

```text
A-time-auth-44192 = time(id=T-auth_44192,event=A-path-auth-token-44192,at=2026-04-20T13:14:02Z)
A-observed-auth-44192 = observed(id=OBS-auth_44192,asserts=A-path-auth-token-44192,by=Entra-ID-01,time=A-time-auth-44192,within=Identity-Scope)

A-time-open-44192 = time(id=T-open_44192,event=A-path-user-open-44192,at=2026-04-20T13:14:03Z)
A-observed-open-44192 = observed(id=OBS-open_44192,asserts=A-path-user-open-44192,by=Priya-Nair,time=A-time-open-44192,within=Azure-Tenant-Scope)

A-time-open-shipment-44192 = time(id=T-open_shipment_44192,event=A-path-open-shipment-44192,at=2026-04-20T13:14:03Z)
A-observed-open-shipment-44192 = observed(id=OBS-open_shipment_44192,asserts=A-path-open-shipment-44192,by=OpsPortal-Web-01,time=A-time-open-shipment-44192,within=Azure-Tenant-Scope)

A-time-query-gateway-44192 = time(id=T-query_gateway_44192,event=A-path-query-gateway-44192,at=2026-04-20T13:14:03Z)
A-observed-query-gateway-44192 = observed(id=OBS-query_gateway_44192,asserts=A-path-query-gateway-44192,by=OpsPortal-Web-01,time=A-time-query-gateway-44192,within=Azure-Tenant-Scope)

A-time-query-integration-44192 = time(id=T-query_integration_44192,event=A-path-query-integration-44192,at=2026-04-20T13:14:03Z)
A-observed-query-integration-44192 = observed(id=OBS-query_integration_44192,asserts=A-path-query-integration-44192,by=APIManagement-OPS-01,time=A-time-query-integration-44192,within=Azure-Tenant-Scope)

A-time-query-tms-44192 = time(id=T-query_tms_44192,event=A-path-query-tms-44192,at=2026-04-20T13:14:04Z)
A-observed-query-tms-44192 = observed(id=OBS-query_tms_44192,asserts=A-path-query-tms-44192,by=AKS-IntegrationHub-01,time=A-time-query-tms-44192,within=Private-WAN)

A-time-read-sql-44192 = time(id=T-read_sql_44192,event=A-path-read-sql-44192,at=2026-04-20T13:14:04Z)
A-observed-read-sql-44192 = observed(id=OBS-read_sql_44192,asserts=A-path-read-sql-44192,by=TMS-Core-01,time=A-time-read-sql-44192,within=Datacenter-Scope)

A-time-return-sql-44192 = time(id=T-return_sql_44192,event=A-path-return-sql-44192,at=2026-04-20T13:14:04Z)
A-observed-return-sql-44192 = observed(id=OBS-return_sql_44192,asserts=A-path-return-sql-44192,by=TMS-Core-01,time=A-time-return-sql-44192,within=Private-WAN)

A-time-query-telemetry-44192 = time(id=T-query_telemetry_44192,event=A-path-query-telemetry-44192,at=2026-04-20T13:14:05Z)
A-observed-query-telemetry-44192 = observed(id=OBS-query_telemetry_44192,asserts=A-path-query-telemetry-44192,by=AKS-IntegrationHub-01,time=A-time-query-telemetry-44192,within=Private-WAN)

A-time-read-telemetry-44192 = time(id=T-read_telemetry_44192,event=A-path-read-telemetry-44192,at=2026-04-20T13:14:05Z)
A-observed-read-telemetry-44192 = observed(id=OBS-read_telemetry_44192,asserts=A-path-read-telemetry-44192,by=Telemetry-API-01,time=A-time-read-telemetry-44192,within=AWS-Tenant-Scope)

A-time-return-telemetry-44192 = time(id=T-return_telemetry_44192,event=A-path-return-telemetry-44192,at=2026-04-20T13:14:05Z)
A-observed-return-telemetry-44192 = observed(id=OBS-return_telemetry_44192,asserts=A-path-return-telemetry-44192,by=Telemetry-API-01,time=A-time-return-telemetry-44192,within=Private-WAN)

A-time-return-view-44192 = time(id=T-return_view_44192,event=A-path-return-view-44192,at=2026-04-20T13:14:06Z)
A-observed-return-view-44192 = observed(id=OBS-return_view_44192,asserts=A-path-return-view-44192,by=AKS-IntegrationHub-01,time=A-time-return-view-44192,within=Azure-Tenant-Scope)

A-time-render-user-44192 = time(id=T-render_user_44192,event=A-path-render-user-44192,at=2026-04-20T13:14:06Z)
A-observed-render-user-44192 = observed(id=OBS-render_user_44192,asserts=A-path-render-user-44192,by=OpsPortal-Web-01,time=A-time-render-user-44192,within=Azure-Tenant-Scope)
```

### Moves vocabulary

```text
auth_token
shipment_request
shipment_query
shipment_record
telemetry_query
telemetry_summary
combined_view
```

---

## Part 2: Replay Into Plain Language

### Structural replay

- Scope Corporate-Operations exists.
- Scope Datacenter-Scope exists.
- Scope Azure-Tenant-Scope exists.
- Scope AWS-Tenant-Scope exists.
- Scope Private-WAN exists.
- Scope Identity-Scope exists.
- Scope Production exists.
- Scope Business-Hours exists.
- Structural Thing Dispatch-Planner exists.
- Structural Thing Shipment exists.
- Structural Thing OpsPortal-Web exists.
- Structural Thing APIManagement-OPS exists.
- Structural Thing AKS-IntegrationHub exists.
- Structural Thing TMS-Core exists.
- Structural Thing SQL-TMS exists.
- Structural Thing Telemetry-API exists.
- Structural Thing Aurora-Fleet exists.
- Structural Thing Entra-ID exists.
- Structural Path auth_token_delivery connects Entra-ID to OpsPortal-Web within Scope Identity-Scope.
- Structural Path user_open_shipment connects Dispatch-Planner to OpsPortal-Web within Scope Azure-Tenant-Scope.
- Structural Path open_shipment_record connects OpsPortal-Web to Shipment within Scope Azure-Tenant-Scope.
- Structural Path query_gateway connects OpsPortal-Web to APIManagement-OPS within Scope Azure-Tenant-Scope.
- Structural Path query_integration connects APIManagement-OPS to AKS-IntegrationHub within Scope Azure-Tenant-Scope.
- Structural Path query_tms connects AKS-IntegrationHub to TMS-Core within Scope Private-WAN.
- Structural Path read_shipment_record connects SQL-TMS to TMS-Core within Scope Datacenter-Scope.
- Structural Path return_shipment_record connects TMS-Core to AKS-IntegrationHub within Scope Private-WAN.
- Structural Path query_telemetry connects AKS-IntegrationHub to Telemetry-API within Scope Private-WAN.
- Structural Path read_telemetry_summary connects Aurora-Fleet to Telemetry-API within Scope AWS-Tenant-Scope.
- Structural Path return_telemetry_summary connects Telemetry-API to AKS-IntegrationHub within Scope Private-WAN.
- Structural Path return_unified_view connects AKS-IntegrationHub to OpsPortal-Web within Scope Azure-Tenant-Scope.
- Structural Path render_unified_view connects OpsPortal-Web to Dispatch-Planner within Scope Azure-Tenant-Scope.
- Constraint auth_required restricts user_open_shipment within Scope Identity-Scope.
- Constraint tms_authoritative restricts read_shipment_record within Scope Datacenter-Scope.
- Constraint telemetry_readonly restricts return_telemetry_summary within Scope AWS-Tenant-Scope.
- Constraint private_wan_only_tms_query restricts query_tms within Scope Private-WAN.
- Constraint private_wan_only_tms_return restricts return_shipment_record within Scope Private-WAN.
- Constraint private_wan_only_telemetry_query restricts query_telemetry within Scope Private-WAN.
- Constraint private_wan_only_telemetry_return restricts return_telemetry_summary within Scope Private-WAN.
- Constraint response_within_5s restricts render_unified_view within Scope Production.
- Constraint business_hours_access restricts user_open_shipment within Scope Business-Hours.

### Instance replay

- Thing Priya-Nair exists as instance of Dispatch-Planner.
- Thing SH-44192 exists as instance of Shipment.
- Thing OpsPortal-Web-01 exists as instance of OpsPortal-Web.
- Thing APIManagement-OPS-01 exists as instance of APIManagement-OPS.
- Thing AKS-IntegrationHub-01 exists as instance of AKS-IntegrationHub.
- Thing TMS-Core-01 exists as instance of TMS-Core.
- Thing SQL-TMS-01 exists as instance of SQL-TMS.
- Thing Telemetry-API-01 exists as instance of Telemetry-API.
- Thing Aurora-Fleet-01 exists as instance of Aurora-Fleet.
- Thing Entra-ID-01 exists as instance of Entra-ID.
- Thing Priya-Nair exists within Scope Corporate-Operations.
- Thing Priya-Nair exists within Scope Business-Hours.
- Thing SH-44192 exists within Scope Production.
- Thing OpsPortal-Web-01 exists within Scope Azure-Tenant-Scope.
- Thing APIManagement-OPS-01 exists within Scope Azure-Tenant-Scope.
- Thing AKS-IntegrationHub-01 exists within Scope Azure-Tenant-Scope.
- Thing TMS-Core-01 exists within Scope Datacenter-Scope.
- Thing SQL-TMS-01 exists within Scope Datacenter-Scope.
- Thing Telemetry-API-01 exists within Scope AWS-Tenant-Scope.
- Thing Aurora-Fleet-01 exists within Scope AWS-Tenant-Scope.
- Thing Entra-ID-01 exists within Scope Identity-Scope.
- Path auth_token_delivery_44192 connects Entra-ID-01 to OpsPortal-Web-01 within Scope Identity-Scope.
- Path user_open_shipment_44192 connects Priya-Nair to OpsPortal-Web-01 within Scope Azure-Tenant-Scope.
- Path open_shipment_record_44192 connects OpsPortal-Web-01 to SH-44192 within Scope Azure-Tenant-Scope.
- Path query_gateway_44192 connects OpsPortal-Web-01 to APIManagement-OPS-01 within Scope Azure-Tenant-Scope.
- Path query_integration_44192 connects APIManagement-OPS-01 to AKS-IntegrationHub-01 within Scope Azure-Tenant-Scope.
- Path query_tms_44192 connects AKS-IntegrationHub-01 to TMS-Core-01 within Scope Private-WAN.
- Path read_shipment_record_44192 connects SQL-TMS-01 to TMS-Core-01 within Scope Datacenter-Scope.
- Path return_shipment_record_44192 connects TMS-Core-01 to AKS-IntegrationHub-01 within Scope Private-WAN.
- Path query_telemetry_44192 connects AKS-IntegrationHub-01 to Telemetry-API-01 within Scope Private-WAN.
- Path read_telemetry_summary_44192 connects Aurora-Fleet-01 to Telemetry-API-01 within Scope AWS-Tenant-Scope.
- Path return_telemetry_summary_44192 connects Telemetry-API-01 to AKS-IntegrationHub-01 within Scope Private-WAN.
- Path return_unified_view_44192 connects AKS-IntegrationHub-01 to OpsPortal-Web-01 within Scope Azure-Tenant-Scope.
- Path render_unified_view_44192 connects OpsPortal-Web-01 to Priya-Nair within Scope Azure-Tenant-Scope.

### Observation replay

- Path auth_token_delivery_44192 occurred at Time 2026-04-20T13:14:02Z.
- Observation OBS-auth_44192 records that Path auth_token_delivery_44192 occurred at Time 2026-04-20T13:14:02Z by Entra-ID-01 within Scope Identity-Scope.
- Path user_open_shipment_44192 occurred at Time 2026-04-20T13:14:03Z.
- Observation OBS-open_44192 records that Path user_open_shipment_44192 occurred at Time 2026-04-20T13:14:03Z by Priya-Nair within Scope Azure-Tenant-Scope.
- Path open_shipment_record_44192 occurred at Time 2026-04-20T13:14:03Z.
- Observation OBS-open_shipment_44192 records that Path open_shipment_record_44192 occurred at Time 2026-04-20T13:14:03Z by OpsPortal-Web-01 within Scope Azure-Tenant-Scope.
- Path query_gateway_44192 occurred at Time 2026-04-20T13:14:03Z.
- Observation OBS-query_gateway_44192 records that Path query_gateway_44192 occurred at Time 2026-04-20T13:14:03Z by OpsPortal-Web-01 within Scope Azure-Tenant-Scope.
- Path query_integration_44192 occurred at Time 2026-04-20T13:14:03Z.
- Observation OBS-query_integration_44192 records that Path query_integration_44192 occurred at Time 2026-04-20T13:14:03Z by APIManagement-OPS-01 within Scope Azure-Tenant-Scope.
- Path query_tms_44192 occurred at Time 2026-04-20T13:14:04Z.
- Observation OBS-query_tms_44192 records that Path query_tms_44192 occurred at Time 2026-04-20T13:14:04Z by AKS-IntegrationHub-01 within Scope Private-WAN.
- Path read_shipment_record_44192 occurred at Time 2026-04-20T13:14:04Z.
- Observation OBS-read_sql_44192 records that Path read_shipment_record_44192 occurred at Time 2026-04-20T13:14:04Z by TMS-Core-01 within Scope Datacenter-Scope.
- Path return_shipment_record_44192 occurred at Time 2026-04-20T13:14:04Z.
- Observation OBS-return_sql_44192 records that Path return_shipment_record_44192 occurred at Time 2026-04-20T13:14:04Z by TMS-Core-01 within Scope Private-WAN.
- Path query_telemetry_44192 occurred at Time 2026-04-20T13:14:05Z.
- Observation OBS-query_telemetry_44192 records that Path query_telemetry_44192 occurred at Time 2026-04-20T13:14:05Z by AKS-IntegrationHub-01 within Scope Private-WAN.
- Path read_telemetry_summary_44192 occurred at Time 2026-04-20T13:14:05Z.
- Observation OBS-read_telemetry_44192 records that Path read_telemetry_summary_44192 occurred at Time 2026-04-20T13:14:05Z by Telemetry-API-01 within Scope AWS-Tenant-Scope.
- Path return_telemetry_summary_44192 occurred at Time 2026-04-20T13:14:05Z.
- Observation OBS-return_telemetry_44192 records that Path return_telemetry_summary_44192 occurred at Time 2026-04-20T13:14:05Z by Telemetry-API-01 within Scope Private-WAN.
- Path return_unified_view_44192 occurred at Time 2026-04-20T13:14:06Z.
- Observation OBS-return_view_44192 records that Path return_unified_view_44192 occurred at Time 2026-04-20T13:14:06Z by AKS-IntegrationHub-01 within Scope Azure-Tenant-Scope.
- Path render_unified_view_44192 occurred at Time 2026-04-20T13:14:06Z.
- Observation OBS-render_user_44192 records that Path render_unified_view_44192 occurred at Time 2026-04-20T13:14:06Z by OpsPortal-Web-01 within Scope Azure-Tenant-Scope.

---

## Part 3: Validation Checks

### Structure vs observation

- Structure exists before observation.
- Hybrid movement is described by instance paths.
- Observation records those paths after they occurred.
- Observation does not create applications, scopes, or paths.

### Constraint check

- `auth_required` applies to `user_open_shipment`.
- `tms_authoritative` applies to `read_shipment_record`.
- `telemetry_readonly` applies to `return_telemetry_summary`.
- `private_wan_only_tms_query` applies to `query_tms`.
- `private_wan_only_tms_return` applies to `return_shipment_record`.
- `private_wan_only_telemetry_query` applies to `query_telemetry`.
- `private_wan_only_telemetry_return` applies to `return_telemetry_summary`.
- `response_within_5s` applies to `render_unified_view`.
- `business_hours_access` applies to `user_open_shipment`.

Observed order:
1. Authentication delivered at `2026-04-20T13:14:02Z`.
2. User request opened at `2026-04-20T13:14:03Z`.
3. Datacenter retrieval observed at `2026-04-20T13:14:04Z`.
4. AWS retrieval observed at `2026-04-20T13:14:05Z`.
5. Unified view rendered at `2026-04-20T13:14:06Z`.

Result:
- Authentication precedes user access.
- Shipment master data is returned from the datacenter record path.
- Telemetry movement remains query-and-return only.
- Cross-environment retrieval occurs through `Private-WAN`.
- End-to-end render completes in 3 seconds from open to render.
- User access occurs within `Business-Hours`.

### Identity check

- `Priya-Nair` is identified by `employee_id`.
- `SH-44192` is identified by `shipment_id`.
- `OpsPortal-Web-01` is identified by `service_name`.
- `APIManagement-OPS-01` is identified by `service_name`.
- `AKS-IntegrationHub-01` is identified by `service_name`.
- `TMS-Core-01` is identified by `service_name`.
- `Telemetry-API-01` is identified by `service_name`.
- `Entra-ID-01` is identified by `service_name`.
- `SQL-TMS-01` is identified by `db_name`.
- `Aurora-Fleet-01` is identified by `db_name`.

---

## Part 4: Projection Mapping

### Things

- `Priya-Nair` becomes person object.
- `SH-44192` becomes shipment object.
- `OpsPortal-Web-01` becomes Azure application object.
- `TMS-Core-01` becomes datacenter application object.
- `Telemetry-API-01` becomes AWS application object.
- `SQL-TMS-01` and `Aurora-Fleet-01` become database objects.

### Scopes

- `Datacenter-Scope` becomes one physical plane.
- `Azure-Tenant-Scope` becomes one cloud plane.
- `AWS-Tenant-Scope` becomes one cloud plane.
- `Private-WAN` becomes one routed corridor between planes.
- `Identity-Scope` becomes one authentication overlay.

### Paths

- `user_open_shipment_44192` becomes entry path into Azure.
- `open_shipment_record_44192` becomes shipment-selection path in Azure.
- `query_tms_44192` and `read_shipment_record_44192` become datacenter retrieval path.
- `return_shipment_record_44192` becomes datacenter return path.
- `query_telemetry_44192` and `read_telemetry_summary_44192` become AWS retrieval path.
- `return_telemetry_summary_44192` becomes AWS return path.
- `return_unified_view_44192` and `render_unified_view_44192` become response path back to user.

### Observed

- `OBS-auth_44192` becomes authentication marker.
- `OBS-open_shipment_44192` becomes shipment-selection marker.
- `OBS-query_tms_44192`, `OBS-read_sql_44192`, and `OBS-return_sql_44192` become datacenter retrieval overlays.
- `OBS-query_telemetry_44192`, `OBS-read_telemetry_44192`, and `OBS-return_telemetry_44192` become AWS retrieval overlays.
- `OBS-render_user_44192` becomes final render highlight.

### Constraints

- `auth_required` blocks entry path until authentication observation exists.
- `tms_authoritative` emphasizes datacenter master-data route.
- `telemetry_readonly` constrains the telemetry return path to read-only summary movement.
- `private_wan_only_tms_query` restricts TMS query path placement.
- `private_wan_only_tms_return` restricts TMS return path placement.
- `private_wan_only_telemetry_query` restricts telemetry query path placement.
- `private_wan_only_telemetry_return` restricts telemetry return path placement.
- `response_within_5s` adds time indicator to full traversal.
- `business_hours_access` constrains user access to the Business-Hours state.

### Time

- `T-auth_44192` through `T-render_user_44192` order the hybrid request.
- Scrubbing time reveals Azure entry, datacenter read, AWS read, and unified render in sequence.

---

## Part 5: Reality Check

- Every line is one parseable assertion.
- Every environment element maps to a primitive, not an explanatory concept.
- Every visual element can trace back to one or more assertions.
- The same assertion set supports infrastructure, operations, and application views.
