"""Thin signal delegate for application audit append/verification."""

from src.services.audit import AuditLog, AuditRecord


def append_audit(log: AuditLog, **kwargs) -> AuditRecord:
    return log.append(**kwargs)


def verify_audit(log: AuditLog) -> bool:
    return log.verify()


__all__ = ["AuditLog", "AuditRecord", "append_audit", "verify_audit"]
