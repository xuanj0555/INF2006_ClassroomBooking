# Roomly API Specification

## 1. Overview

Roomly provides a classroom/study-room booking service.

The backend is responsible for:

- authentication checks
- authorisation
- room validation
- participant validation
- capacity validation
- booking conflict prevention
- booking limits
- cancellation
- attendance/check-in
- persistent storage

The frontend must not be trusted to enforce booking rules.

---

# 2. API Base

Local development:

```text
http://127.0.0.1:8765/api