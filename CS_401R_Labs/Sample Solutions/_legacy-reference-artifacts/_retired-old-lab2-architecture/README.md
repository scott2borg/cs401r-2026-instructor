# Retired — pre-2026-07 Lab 2 architecture

These files implement the **original** Lab 2 design: Kinesis streaming ingestion,
S3-event-driven Lambda, a five-dataset synthetic corpus, and a customer-level
feature pipeline built on top of it.

Lab 2 was rebuilt in July 2026 around a simpler and fully-verified design:

    raw/customers/ (one transaction CSV)
      -> Glue crawler -> catalog
      -> Glue job `transform`         -> processed/customers/  (transaction grain)
      -> Glue job `feature-engineer`  -> features/customers/   (customer grain)
                                      -> SageMaker Feature Store

Nothing here is referenced by the current `Lab_2.md`, by `modules/glue/`, or by
`modules/feature_store/`. It is kept only because parts of it (the streaming and
event-driven ingestion patterns in particular) may be useful source material for
a later lab or for the team project.

**Do not grade against these files.** The authoritative Lab 2 implementation is
`data/glue-scripts/` plus `infrastructure/modules/{glue,feature_store}/`.
