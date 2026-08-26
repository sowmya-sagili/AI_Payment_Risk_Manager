# Graph Risk Intelligence

## Graph Data Model
The system uses NetworkX to model entities as nodes and relationships as edges.
### Entities
- CUSTOMER
- DEVICE
- IP
- PAYMENT_ACCOUNT
- TRANSACTION

### Relationships
- CUSTOMER -> TRANSACTION
- CUSTOMER -> DEVICE
- TRANSACTION -> IP

## Risk Scoring
The Graph Engine identifies connected components (clusters) in the network.
- **Shared Device**: +30
- **Shared Payment Account**: +40
- **Shared IP**: +20
- **Large Cluster (>2 Customers)**: +20

## Aggregation
The Risk Aggregator combines:
- ML Score (50%)
- Velocity Score (25%)
- Graph Score (25%)

If graph identifiers are unavailable, the weights smoothly re-normalize to preserve system stability (e.g. ML 66%, Velocity 33%).

## Limitations
Currently relies on in-memory NetworkX caching rebuilt from SQLite for scale. In production, this can seamlessly transition to Neo4j.
