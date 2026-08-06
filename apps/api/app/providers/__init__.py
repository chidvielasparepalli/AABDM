"""Provider abstraction layer.

Interfaces (Protocols) only — every external service the platform touches is
abstracted here. Adapters implement these contracts; business logic depends
only on the interfaces, so providers are swappable without code changes.

Current state: interfaces defined, no implementations. The default adapters
(rule-based research, simulator voice, log messaging) arrive as the first
implementations and reproduce today's behavior. LLM default is a no-op that
defers to the rule-based pipeline — turning LLM on never breaks the system,
it only makes it smarter.
"""
