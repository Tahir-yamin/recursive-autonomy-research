# BL-13 — AWS Architect Critiques

**Priority:** 🟠 P1
**Status:** OPEN
**Audit date:** 2026-06-07
**Grade given:** Fail | Verdict: Reject

---

## Issue 13.1 — §7.2 Cloud Claims are 100% Prose, Zero Code
**File:** main.tex:484–490
**Evidence (grep result):** Zero occurrences across all .py files of:
`BaseStateStore`, `BaseDistributedLock`, `RedisLock`, `SQSClient`,
`KafkaProducer`, `boto3`, `redis`, `sqs`, `kafka`, `lambda_handler`

**Claimed but not implemented:**
1. Redis Redlock distributed locking
2. Amazon DynamoDB / S3 WAL storage
3. SQS/Kafka message queues for consolidation events
4. AWS Lambda-compatible stateless worker shape
5. `BaseStateStore` interface class
6. `BaseDistributedLock` interface class

**Fix (minimum viable for a Q1 paper):**
Add stub interface classes to `run_pilot_experiment.py`:
```python
from abc import ABC, abstractmethod

class BaseStateStore(ABC):
    """Abstract interface for WAL persistence backends.
    Default: local filesystem. Cloud: S3/DynamoDB adapter."""
    @abstractmethod
    def save(self, key: str, state: dict) -> None: ...
    @abstractmethod
    def load(self, key: str) -> dict | None: ...
    @abstractmethod
    def delete(self, key: str) -> None: ...

class LocalFileStateStore(BaseStateStore):
    """Concrete local-filesystem adapter (current implementation)."""
    def save(self, key: str, state: dict) -> None:
        save_wal(key, ...)  # existing logic
    def load(self, key: str) -> dict | None:
        return load_wal(key)
    def delete(self, key: str) -> None:
        clear_wal(key)

class BaseDistributedLock(ABC):
    """Abstract interface for distributed locks.
    Default: no-op (single process). Cloud: Redis Redlock adapter."""
    @abstractmethod
    def acquire(self, resource: str, ttl_ms: int) -> bool: ...
    @abstractmethod
    def release(self, resource: str) -> None: ...

class NoOpLock(BaseDistributedLock):
    """Single-process no-op lock (current implementation)."""
    def acquire(self, resource: str, ttl_ms: int) -> bool: return True
    def release(self, resource: str) -> None: pass
```
Then update §7.2 to reference these classes by name with file:line.

**Acceptance criteria:**
- [ ] `BaseStateStore` and `BaseDistributedLock` exist in code
- [ ] `LocalFileStateStore` and `NoOpLock` are the concrete adapters
- [ ] §7.2 references these classes with file:line citations
- [ ] Section uses future-tense for Redis/SQS/Lambda ("could be
      extended to Redis Redlock" not "is implemented with Redis Redlock")

---

## Issue 13.2 — Redlock Proposed for Correctness-Critical Use Case
**Evidence:** Kleppmann (2016) demonstrates Redlock is unsafe for
correctness-critical mutual exclusion (GC pauses, clock skew, no
fencing tokens). The paper proposes it for "preventing state race
conditions" — exactly the use case Kleppmann says it fails.

**Fix:** Either switch recommendation to ZooKeeper/etcd (consensus-
based, correctness-safe) or add a caveat:
"Note: Redlock provides probabilistic safety guarantees and is
appropriate for efficiency-critical (not correctness-critical)
locking. For correctness-critical scenarios, consensus-based locks
(etcd, ZooKeeper) are recommended [Kleppmann 2016]."
Add `\bibitem` for Kleppmann (2016):
```latex
\bibitem[Kleppmann(2016)]{kleppmann2016redlock}
M. Kleppmann.
\newblock How to do distributed locking.
\newblock \url{https://martin.kleppmann.com/2016/02/08/
how-to-do-distributed-locking.html}, 2016.
```

**Acceptance criteria:**
- [ ] Redlock limitations acknowledged in §7.2
- [ ] Kleppmann (2016) cited
