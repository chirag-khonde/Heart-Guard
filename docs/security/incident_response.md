# HeartGuard — Security Incident Response Playbook

**Document Version:** 1.0.0  
**Phase:** 15 (Security, Privacy, Audit Logging & Compliance)  
**Applicability:** HeartGuard Platform Operators & Administrators  

---

## 1. Overview & Objectives

This playbook outlines the operational procedures for responding to security incidents on the HeartGuard platform. Immediate priorities during an incident are:
1. Preventing unauthorized exposure of patient medical assessments.
2. Isolating compromised accounts or compromised system components.
3. Preserving immutable audit logs for forensic analysis.
4. Restoring verified, secure operations without data loss.

---

## 2. 7-Step Incident Response Lifecycle

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ 1. Identification│ ───► │  2. Containment  │ ───► │ 3. Investigation │
└──────────────────┘      └──────────────────┘      └─────────┬────────┘
                                                              │
┌──────────────────┐      ┌──────────────────┐      ┌─────────▼────────┐
│  6. Restoration  │ ◄─── │  5. Rotation     │ ◄─── │ 4. Audit Review  │
└────────┬─────────┘      └──────────────────┘      └──────────────────┘
         │
┌────────▼─────────────────┐
│ 7. Post-Mortem & Docs    │
└──────────────────────────┘
```

### Step 1: Identification & Alerting
- **Trigger Sources:**
  - Automated high/critical alerts in `data/security/audit.db` (`HIGH` or `CRITICAL` severity events).
  - Rapid spikes in `access_denied` or `idor_attempt` records.
  - Rate limiter blocks on authentication routes (`RATE_LIMIT_EXCEEDED`).
  - Report of anomalous clinical recommendations or unauthorized password change.
- **Immediate Action:** The incident coordinator verifies whether the alert represents a false positive or an active exploit attempt.

### Step 2: Immediate Containment
- **Account Isolation:**
  - If a specific user account is compromised, deactivate it immediately via `UserRepository.toggle_user_active(user_id, is_active=False)`.
  - Invalidate active sessions by purging session state or clearing memory token tables.
- **Service Isolation:**
  - If database or server compromise is suspected, set `DEMO_MODE=True` and take the web gateway offline behind an HTTP 503 maintenance banner.
  - Block offending IP addresses at the reverse proxy (nginx/Cloudflare) layer.

### Step 3: Forensic Investigation
- Secure snapshots of:
  - `data/security/audit.db`
  - Web server access logs (`/var/log/nginx/access.log`)
  - Application logs (`logs/heartguard.log`)
- Reconstruct the attack timeline: identify entry point, requested URIs, manipulated payloads, and affected patient IDs.

### Step 4: Audit Review & Impact Assessment
- Execute targeted audit queries via `src.security.audit_logger.get_filtered_events`:
  - Review all `login_failure`, `access_denied`, `idor_attempt`, and `role_changed` events within the incident window.
  - Cross-reference with `resource_id` fields to compile a definitive list of compromised or inspected assessment records.
- Determine if PII or clinical evaluations were exfiltrated.

### Step 5: Credential & Secret Rotation
- If secrets or environment variables were exposed:
  - Rotate Twilio credentials (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`).
  - Rotate platform `SECRET_KEY` and invalid session cookies.
  - Trigger forced password resets for affected user accounts using salted Bcrypt hashes.
  - Ensure updated credentials are injected strictly through platform environment variables.

### Step 6: Service Restoration & Verification
- Verify database integrity: ensure no unauthorized rows in `users.db` or alterations in `history.db`.
- Validate that all automated test suites pass (`pytest -v`).
- Re-enable the web gateway.
- Monitor live traffic and the Security Center (`pages/security.py`) closely for recurring anomalous patterns.

### Step 7: Post-Mortem & Documentation
- Conduct a blameless post-mortem within 48 hours.
- Document:
  - Root cause analysis (RCA).
  - Time to detect (TTD) and time to contain (TTC).
  - Remediation actions taken and required codebase patches.
- Update `threat_model.md` and test coverage to prevent regression of the specific attack vector.
