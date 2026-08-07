"""Event bus — the platform's nervous system.

All cross-module communication flows through events. The bus is the single
point of truth for decoupling: producers emit facts, subscribers react.
No component ever calls another component's internals.
"""