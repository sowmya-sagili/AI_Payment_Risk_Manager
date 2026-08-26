# Adaptive Risk Decision Engine

## Overview
The Decision Engine (ackend/services/decision_engine.py) sits at the end of the risk assessment pipeline. It replaces flat aggregation with an intelligent, rules-driven system that acts deterministically based on input signals.

## Evaluation Priority
1. **Critical Circuit Breakers**: Overrides all other scoring if a single vector is critically high.
2. **Combination Rules**: Escalates risk if multiple vectors show moderate-to-high risk concurrently.
3. **Adaptive Weighted Decision**: Safely aggregates available signals using dynamic weighting (w_ml, w_vel, w_grph).

## Adaptive Weighting Behavior
- Normal: ML: 50%, Velocity: 25%, Graph: 25%
- Graph Missing: ML: 67%, Velocity: 33%
- Velocity Missing: ML: 67%, Graph: 33%
- Both Missing: ML: 100%

## Decision Modes
- NORMAL: No rules triggered. Used base adaptive weighting.
- RULE_OVERRIDE: Triggered by multi-vector combination logic.
- CIRCUIT_BREAKER: Triggered by an absolutely critical singular risk factor.

## Audit Logging
All transactions log their exact weights, decision_mode, and deterministic decision_reason inside SQLite for compliance.
