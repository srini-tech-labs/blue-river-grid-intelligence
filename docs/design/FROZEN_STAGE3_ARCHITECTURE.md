# Blue River Power — Frozen Stage 3 Architecture

```text
Synthetic Blue River Power source world
                |
                v
             Amazon S3
       structured + PDFs
                |
        +-------+-------+
        |               |
        v               v
     Lakeflow       ai_parse_document
  Auto Loader       ai_prep_search
        |               |
        v               v
 Bronze/Silver/Gold  document_chunks
        |               |
        |               v
        |        Databricks AI Search
        |        / Vector Search
        |        HYBRID + filters
        |               |
        +-------+-------+
                |
                v
        Hybrid context assembly
          [S1] + [D1]...[Dn]
                |
                v
       Databricks system.ai model
          via ai_query(...)
                |
                v
       Grounded answer + citations
                |
                v
       Retrieval/grounding evaluation
```

## Structured data role

Structured facts stay in Delta and are retrieved deterministically. They are not unnecessarily embedded into a vector database.

Primary structured products:

- `workspace.brp_gold.asset_operational_summary`
- `workspace.brp_gold.asset_event_timeline`
- `workspace.brp_gold.reliability_kpis`
- `workspace.brp_gold.maintenance_summary`
- `workspace.brp_silver.outage_events`
- `workspace.brp_silver.work_orders`

## Unstructured knowledge role

Enterprise-style PDFs are parsed and prepared natively in Databricks, then indexed using Delta Sync.

Primary knowledge products:

- `workspace.brp_knowledge.document_chunks`
- AI Search endpoint recorded in `stage2_runtime_metadata`
- `workspace.brp_knowledge.utility_knowledge_index`

## Stage 3 products

- `workspace.brp_knowledge.stage3_latest_context`
- `workspace.brp_knowledge.stage3_latest_answer`
- `workspace.brp_knowledge.stage3_retrieval_evaluation`
- `workspace.brp_knowledge.stage3_validation_result`
- `workspace.brp_knowledge.stage3_release_manifest`
- `workspace.brp_knowledge.stage3_release_inventory`

## Design principle

The application layer should retrieve numerical and operational facts from Delta and documentary evidence from AI Search, then combine them at answer-generation time.

The application must not replace the Databricks retrieval architecture with an in-memory vector database or a second search stack.
