"""Attendance API routes"""
from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from ..extensions import db, limiter
from ..models import Attendance, Course, User
from ..compliance.audit import log_audit
from . import attendance_bp


@attendance_bp.route('/history', methods=['GET'])
@login_required
def history():
    """Get attendance history for CURRENT logged-in user ONLY"""
    try:
        # Query parameters for filtering
        course_id = request.args.get('course_id', type=int)
        start_date = request.args.get('start_date', type=lambda d: datetime.strptime(d, '%Y-%m-%d'))
        end_date = request.args.get('end_date', type=lambda d: datetime.strptime(d, '%Y-%m-%d'))
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        
        # CRITICAL: Filter by CURRENT logged-in user ONLY
        query = Attendance.query.filter(
            Attendance.user_id == current_user.id,
            Attendance.status != 'deleted'
        )
        
        # Apply additional filters if provided
        if course_id:
            query = query.filter(Attendance.course_id == course_id)
        if start_date:
            query = query.filter(Attendance.timestamp >= start_date)
        if end_date:
            query = query.filter(Attendance.timestamp <= end_date + timedelta(days=1))
        
        # Order by newest first
        query = query.order_by(Attendance.timestamp.desc())
        
        # Paginate results
        records = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Format response with all academic information
        records_data = []
        for record in records.items:
            records_data.append({
                'id': record.id,
                'course': {
                    'code': record.course.code if record.course else record.unit_code,
                    'name': record.course.name if record.course else f"{record.unit_code} - {record.course_program or 'General'}",
                    'department': record.course.department if record.course else record.course_program
                },
                'timestamp': record.timestamp.isoformat(),
                'year_of_study': record.year_of_study or current_user.year_of_study,
                'course_program': record.course_program or current_user.course_program,
                'unit_code': record.unit_code,
                'confidence': record.confidence_score,
                'liveness_verified': record.liveness_verified,
                'status': record.status,
                'method': record.match_method
            })
        
        return jsonify({
            'records': records_data,
            'pagination': {
                'page': records.page,
                'per_page': records.per_page,
                'total': records.total,
                'pages': records.pages,
                'has_next': records.has_next,
                'has_prev': records.has_prev,
                'next': f'?page={records.next_num}' if records.has_next else None,
                'prev': f'?page={records.prev_num}' if records.has_prev else None
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"History error: {e}")
        return jsonify({'error': 'Failed to load attendance history'}), 500


@attendance_bp.route('/mark', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def mark():
    """Mark attendance via facial recognition
    
    ✅ Allows:
    - Multiple DIFFERENT units on same day
    - Same unit on DIFFERENT days
    
    ❌ Prevents:
    - Same unit on SAME day (duplicate prevention)
    """
    try:
        data = request.get_json() or request.form.to_dict()
        
        current_app.logger.info(f"Attendance request from user {current_user.id}: {data}")
        
        # Get unit code (accept both parameter names)
        unit_code = data.get('unit_code') or data.get('course_code')
        if not unit_code:
            return jsonify({'error': 'Unit code or course code required'}), 400
        
        year_of_study = data.get('year_of_study', current_user.year_of_study or '1')
        course_program = data.get('course_program', current_user.course_program or '')
        
        # Get or create course (auto-create if doesn't exist)
        course = Course.query.filter_by(code=unit_code, is_active=True).first()
        if not course:
            # Auto-create course - allows ANY valid unit code
            course = Course(
                code=unit_code,
                name=f"{unit_code} - {course_program or 'General'}",
                department=course_program or 'General',
                is_active=True
            )
            db.session.add(course)
            db.session.commit()
            current_app.logger.info(f"Auto-created course: {unit_code}")
        
        # ✅ KEY LOGIC: Check if already marked TODAY for THIS SPECIFIC COURSE
        # This allows: different units same day, same unit different days
        # This prevents: same unit same day (duplicate)
        today = datetime.utcnow().date()
        existing = Attendance.query.filter(
            Attendance.user_id == current_user.id,      # Same student
            Attendance.course_id == course.id,           # Same unit/course
            db.func.date(Attendance.timestamp) == today, # Same date
            Attendance.status != 'deleted'               # Not soft-deleted
        ).first()
        
        if existing:
            return jsonify({
                'status': 'already_marked',
                'message': f'Attendance already recorded at {existing.timestamp}',
                'attendance_id': existing.id
            }), 200
        
        # Create attendance record
        record = Attendance(
            user_id=current_user.id,
            course_id=course.id,
            timestamp=datetime.utcnow(),
            confidence_score=data.get('confidence_score', 0.95),
            liveness_verified=data.get('liveness_verified', True),
            status='present',
            year_of_study=year_of_study,
            course_program=course_program,
            unit_code=unit_code,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        db.session.add(record)
        db.session.commit()
        
        # Audit log for compliance
        log_audit(
            actor_id=current_user.id,
            action='attendance_marked',
            resource_type='attendance',
            resource_id=record.id,
            ip_address=request.remote_addr,
            status_code=201,
            face_match_confidence=data.get('confidence_score', 0.95)
        )
        
        return jsonify({
            'status': 'success',
            'message': f'Attendance marked for {current_user.full_name} - {unit_code}',
            'attendance': {
                'id': record.id,
                'course': course.code,
                'unit_code': unit_code,
                'year_of_study': year_of_study,
                'course_program': course_program,
                'timestamp': record.timestamp.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Mark attendance error: {e}")
        return jsonify({'error': f'Failed to mark attendance: {str(e)}'}), 500


@attendance_bp.route('/course/<int:course_id>', methods=['GET'])
@login_required
def course_attendance(course_id):
    """Get attendance records for a course (instructors/admins ONLY)"""
    try:
        course = Course.query.get_or_404(course_id)
        
        # Permission check - only instructors and admins can view all students
        if current_user.role not in ['admin', 'instructor']:
            return jsonify({'error': 'Unauthorized. Instructors and admins only.'}), 403
        
        # Query parameters
        start_date = request.args.get('start_date', type=lambda d: datetime.strptime(d, '%Y-%m-%d'))
        end_date = request.args.get('end_date', type=lambda d: datetime.strptime(d, '%Y-%m-%d'))
        
        # Base query for this course
        query = Attendance.query.filter(
            Attendance.course_id == course_id,
            Attendance.status == 'present'
        )
        
        # Apply date filters
        if start_date:
            query = query.filter(Attendance.timestamp >= start_date)
        if end_date:
            query = query.filter(Attendance.timestamp <= end_date + timedelta(days=1))
        
        records = query.order_by(Attendance.timestamp.desc()).all()
        
        # Format response
        records_data = []
        for record in records:
            records_data.append({
                'id': record.id,
                'student': {
                    'id': record.student.id,
                    'reg_number': record.student.reg_number,
                    'full_name': record.student.full_name,
                    'year_of_study': record.student.year_of_study,
                    'course_program': record.student.course_program
                },
                'course': course.to_dict(),
                'timestamp': record.timestamp.isoformat(),
                'year_of_study': record.year_of_study,
                'course_program': record.course_program,
                'unit_code': record.unit_code,
                'confidence': record.confidence_score,
                'status': record.status
            })
        
        # Calculate statistics
        unique_students = len(set(r['student']['id'] for r in records_data))
        
        return jsonify({
            'course_id': course_id,
            'course': course.to_dict(),
            'summary': {
                'total_records': len(records_data),
                'unique_students': unique_students,
                'date_range': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                }
            },
            'records': records_data[:100]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Course attendance error: {e}")
        return jsonify({'error': 'Failed to load course attendance'}), 500


@attendance_bp.route('/<int:attendance_id>', methods=['DELETE'])
@login_required
def delete_record(attendance_id):
    """Soft-delete an attendance record (instructors/admins ONLY)"""
    try:
        record = Attendance.query.get_or_404(attendance_id)
        
        # Permission check - only instructors and admins can delete
        if current_user.role not in ['admin', 'instructor']:
            return jsonify({'error': 'Unauthorized. Instructors and admins only.'}), 403
        
        data = request.get_json() or {}
        reason = data.get('reason', 'No reason provided')
        
        # Soft delete (don't actually remove from database)
        record.status = 'deleted'
        record.notes = f"Deleted by {current_user.reg_number}: {reason}"
        db.session.commit()
        
        # Audit log for compliance
        log_audit(
            actor_id=current_user.id,
            action='attendance_deleted',
            resource_type='attendance',
            resource_id=attendance_id,
            ip_address=request.remote_addr,
            status_code=200,
            notes=reason
        )
        
        return jsonify({
            'message': 'Record deleted successfully',
            'record_id': attendance_id,
            'deleted_by': current_user.reg_number
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete attendance error: {e}")
        return jsonify({'error': 'Failed to delete record'}), 500


@attendance_bp.route('/stats', methods=['GET'])
@login_required
def attendance_stats():
    """Get attendance statistics for current user"""
    try:
        # Get total attendance count
        total = Attendance.query.filter(
            Attendance.user_id == current_user.id,
            Attendance.status == 'present'
        ).count()
        
        # Get this month's count
        first_day = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month = Attendance.query.filter(
            Attendance.user_id == current_user.id,
            Attendance.status == 'present',
            Attendance.timestamp >= first_day
        ).count()
        
        # Get unique courses attended
        courses = db.session.query(Attendance.course_id).filter(
            Attendance.user_id == current_user.id,
            Attendance.status == 'present'
        ).distinct().count()
        
        # Get last attendance date
        last = Attendance.query.filter(
            Attendance.user_id == current_user.id,
            Attendance.status == 'present'
        ).order_by(Attendance.timestamp.desc()).first()
        
        return jsonify({
            'total': total,
            'this_month': this_month,
            'unique_courses': courses,
            'last_attendance': last.timestamp.isoformat() if last else None
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Stats error: {e}")
        return jsonify({'error': 'Failed to load statistics'}), 500


# ============================================================================
# INSTRUCTOR/ADMIN ENDPOINTS
# ============================================================================

@attendance_bp.route('/instructor/dashboard', methods=['GET'])
@login_required
def instructor_dashboard():
    """Get instructor dashboard data - all units they teach"""
    try:
        # Only instructors and admins can access
        if current_user.role not in ['admin', 'instructor']:
            return jsonify({'error': 'Unauthorized. Instructors and admins only.'}), 403
        
        # Get all courses this instructor teaches (or all courses for admin)
        if current_user.role == 'instructor':
            courses = Course.query.filter_by(
                instructor_id=current_user.id,
                is_active=True
            ).all()
        else:
            # Admin sees all courses
            courses = Course.query.filter_by(is_active=True).all()
        
        courses_data = []
        for course in courses:
            # Get attendance count for this course
            attendance_count = Attendance.query.filter_by(
                course_id=course.id,
                status='present'
            ).count()
            
            # Get unique students count
            unique_students = db.session.query(Attendance.user_id).filter_by(
                course_id=course.id,
                status='present'
            ).distinct().count()
            
            courses_data.append({
                'id': course.id,
                'code': course.code,
                'name': course.name,
                'department': course.department,
                'instructor_id': course.instructor_id,
                'attendance_count': attendance_count,
                'unique_students': unique_students
            })
        
        return jsonify({
            'instructor': current_user.to_dict(),
            'courses': courses_data,
            'total_courses': len(courses_data)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Instructor dashboard error: {e}")
        return jsonify({'error': 'Failed to load dashboard'}), 500


@attendance_bp.route('/instructor/unit/<unit_code>', methods=['GET'])
@login_required
def get_unit_attendance(unit_code):
    """Get all attendance records for a specific unit code"""
    try:
        # Only instructors and admins
        if current_user.role not in ['admin', 'instructor']:
            return jsonify({'error': 'Unauthorized. Instructors and admins only.'}), 403
        
        # Query parameters for filtering
        year_of_study = request.args.get('year_of_study')
        course_program = request.args.get('course_program')
        start_date = request.args.get('start_date', type=lambda d: datetime.strptime(d, '%Y-%m-%d'))
        end_date = request.args.get('end_date', type=lambda d: datetime.strptime(d, '%Y-%m-%d'))
        
        # Get course by unit code
        course = Course.query.filter_by(code=unit_code).first()
        
        if not course:
            return jsonify({'error': f'Unit {unit_code} not found'}), 404
        
        # Build query
        query = Attendance.query.filter(
            Attendance.course_id == course.id,
            Attendance.status == 'present'
        )
        
        # Apply filters
        if year_of_study:
            query = query.filter(Attendance.year_of_study == year_of_study)
        if course_program:
            query = query.filter(Attendance.course_program == course_program)
        if start_date:
            query = query.filter(Attendance.timestamp >= start_date)
        if end_date:
            query = query.filter(Attendance.timestamp <= end_date + timedelta(days=1))
        
        # Get all records
        records = query.order_by(Attendance.timestamp.desc()).all()
        
        # Format response with student details
        students_data = []
        for record in records:
            students_data.append({
                'id': record.id,
                'student': {
                    'id': record.student.id,
                    'reg_number': record.student.reg_number,
                    'full_name': record.student.full_name,
                    'email': record.student.email,
                    'year_of_study': record.student.year_of_study,
                    'course_program': record.student.course_program
                },
                'attendance': {
                    'timestamp': record.timestamp.isoformat(),
                    'year_of_study': record.year_of_study,
                    'course_program': record.course_program,
                    'unit_code': record.unit_code,
                    'confidence': record.confidence_score,
                    'liveness_verified': record.liveness_verified
                }
            })
        
        # Calculate statistics
        unique_students = len(set(s['student']['id'] for s in students_data))
        
        return jsonify({
            'unit': {
                'code': unit_code,
                'name': course.name,
                'department': course.department
            },
            'filters': {
                'year_of_study': year_of_study,
                'course_program': course_program,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'summary': {
                'total_records': len(students_data),
                'unique_students': unique_students,
                'date_range': {
                    'from': records[-1].timestamp.isoformat() if records else None,
                    'to': records[0].timestamp.isoformat() if records else None
                }
            },
            'students': students_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Unit attendance error: {e}")
        return jsonify({'error': 'Failed to load unit attendance'}), 500


@attendance_bp.route('/instructor/export/<unit_code>', methods=['GET'])
@login_required
def export_attendance(unit_code):
    """Export attendance records to CSV"""
    try:
        import csv
        from io import StringIO
        
        # Only instructors and admins
        if current_user.role not in ['admin', 'instructor']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get course
        course = Course.query.filter_by(code=unit_code).first()
        if not course:
            return jsonify({'error': f'Unit {unit_code} not found'}), 404
        
        # Get attendance records
        records = Attendance.query.filter_by(
            course_id=course.id,
            status='present'
        ).order_by(Attendance.timestamp.desc()).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Reg Number', 'Full Name', 'Email', 'Year of Study',
            'Course Program', 'Attendance Date', 'Time', 'Unit Code',
            'Confidence', 'Status'
        ])
        
        # Data rows
        for record in records:
            writer.writerow([
                record.student.reg_number,
                record.student.full_name,
                record.student.email,
                record.year_of_study or record.student.year_of_study,
                record.course_program or record.student.course_program,
                record.timestamp.strftime('%Y-%m-%d'),
                record.timestamp.strftime('%H:%M:%S'),
                unit_code,
                f"{record.confidence_score * 100:.1f}%",
                record.status
            ])
        
        return jsonify({
            'csv': output.getvalue(),
            'filename': f'{unit_code}_attendance_{datetime.utcnow().strftime("%Y%m%d")}.csv',
            'total_records': len(records)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Export error: {e}")
        return jsonify({'error': 'Failed to export'}), 500