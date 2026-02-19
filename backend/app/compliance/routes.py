"""Compliance API routes"""
from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from ..extensions import db, limiter
from ..models import User, ConsentRecord, AuditLog
from . import compliance_bp
from .audit import get_audit_logs


@compliance_bp.route('/audit-logs', methods=['GET'])
@login_required
def audit_logs():
    """Retrieve audit logs (admin only)"""
    if current_user.role not in ['admin']:
        return jsonify({'error': 'Admin access required'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    
    logs = get_audit_logs(page=page, per_page=per_page)
    
    return jsonify({
        'logs': [log.to_dict() for log in logs.items],
        'pagination': {
            'page': logs.page,
            'total': logs.total,
            'pages': logs.pages
        }
    }), 200


@compliance_bp.route('/data-request', methods=['POST'])
@login_required
@limiter.limit("3 per day")
def data_subject_request():
    """Handle data subject rights requests"""
    data = request.get_json()
    request_type = data.get('type')
    
    valid_types = ['access', 'rectification', 'erasure', 'restriction', 'portability']
    if request_type not in valid_types:
        return jsonify({'error': f'Valid types: {valid_types}'}), 400
    
    from .audit import log_audit
    log_audit(
        actor_id=current_user.id,
        action=f'data_request_{request_type}',
        resource_type='data_subject_request',
        ip_address=request.remote_addr,
        status_code=202
    )
    
    return jsonify({
        'request_id': f"dsr_{current_user.id}_{int(datetime.utcnow().timestamp())}",
        'status': 'received',
        'estimated_response': '30 days per Data Protection Act Section 35'
    }), 202