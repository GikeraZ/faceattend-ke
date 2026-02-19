"""Audit logging utilities"""
from datetime import datetime
from ..extensions import db
from ..models import AuditLog


def log_audit(actor_id=None, action=None, resource_type=None, resource_id=None,
             ip_address=None, user_agent=None, request_method=None, request_path=None,
             status_code=None, error_message=None, face_match_confidence=None,
             liveness_score=None, notes=None):
    """Create immutable audit log entry"""
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method=request_method,
        request_path=request_path,
        status_code=status_code,
        error_message=error_message,
        face_match_confidence=face_match_confidence,
        liveness_score=liveness_score
    )
    
    if notes:
        log.notes = notes[:500]
    
    db.session.add(log)
    db.session.commit()
    
    return log


def get_audit_logs(actor_id=None, action=None, start_date=None, end_date=None,
                  resource_type=None, page=1, per_page=50):
    """Query audit logs with filters"""
    query = AuditLog.query
    
    if actor_id:
        query = query.filter_by(actor_id=actor_id)
    if action:
        query = query.filter_by(action=action)
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    
    return query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )