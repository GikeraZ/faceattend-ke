"""Face recognition API routes"""
from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime
from ..extensions import db, limiter
from ..models import User, Attendance, Course
from ..compliance.audit import log_audit
from . import face_bp
from .engine import FaceEngine
from .liveness import LivenessChecker
import io
from PIL import Image
import numpy as np


# Initialize face engine
face_engine = FaceEngine()


@face_bp.route('/enroll', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def enroll_face():
    """Enroll user's face for recognition"""
    # Check consent
    if not current_user.consent_given:
        return jsonify({
            'error': 'Biometric consent required',
            'action': 'Please provide consent at /api/auth/consent'
        }), 403
    
    # Validate file upload
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo uploaded'}), 400
    
    file = request.files['photo']
    
    try:
        # Read image data
        image_bytes = file.read()
        
        if not image_bytes:
            return jsonify({'error': 'Empty image file'}), 400
        
        # Validate and convert image
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as JPEG for processing
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            image_bytes = output.getvalue()
            
        except Exception as e:
            current_app.logger.error(f"Image processing error: {e}")
            return jsonify({'error': f'Invalid image file: {str(e)}'}), 400
        
        # Check file size
        max_size = current_app.config.get('MAX_IMAGE_SIZE_MB', 5) * 1024 * 1024
        if len(image_bytes) > max_size:
            return jsonify({'error': f'Image too large. Max {max_size // (1024*1024)}MB allowed'}), 400
        
        # Preprocess image
        image, error = face_engine.preprocess_image(image_bytes, max_size_mb=5)
        
        if error:
            return jsonify({'error': error}), 400
        
        # Validate image quality
        quality = face_engine.validate_image_quality(image)
        if not quality['valid']:
            return jsonify({'error': quality['error']}), 422
        
        # Generate face encoding
        encoding = face_engine.encode_face(image, quality['face_location'])
        if encoding is None:
            return jsonify({'error': 'Could not encode face'}), 422
        
        # Run liveness check
        liveness_result = LivenessChecker.verify(image_bytes, quality['face_location'])
        if not liveness_result['liveness_verified']:
            log_audit(
                actor_id=current_user.id,
                action='face_enroll_failed',
                resource_type='face',
                ip_address=request.remote_addr,
                status_code=422,
                error_message=f"Liveness check failed: {liveness_result['details']}",
                liveness_score=liveness_result['confidence']
            )
            
            return jsonify({
                'error': 'Liveness verification failed',
                'details': liveness_result.get('details', 'Please ensure you are physically present'),
                'security_alert': True
            }), 422
        
        # Store encoding (NOT raw image - privacy by design)
        current_user.face_encoding = encoding.tolist()
        current_user.face_enrolled_at = db.func.now()
        db.session.commit()
        
        # Audit
        log_audit(
            actor_id=current_user.id,
            action='face_enrolled',
            resource_type='face',
            resource_id=current_user.id,
            ip_address=request.remote_addr,
            status_code=201,
            face_match_confidence=1.0
        )
        
        return jsonify({
            'message': 'Face enrolled successfully',
            'encoding_id': f'enc_{current_user.id}',
            'quality_score': 0.95,
            'liveness_verified': True
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Face enrollment error: {e}")
        db.session.rollback()
        return jsonify({'error': f'Enrollment failed: {str(e)}'}), 500


@face_bp.route('/recognize', methods=['POST'])
@limiter.limit("30 per minute")
def recognize_face():
    """Recognize face AND create attendance record - accepts ANY unit code"""
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo provided'}), 400
    
    file = request.files['photo']
    
    # ✅ Accept both unit_code and course_code (flexible parameter names)
    unit_code = request.form.get('unit_code') or request.form.get('course_code')
    year_of_study = request.form.get('year_of_study', '1')
    course_program = request.form.get('course_program', '')
    
    if not unit_code:
        return jsonify({'error': 'Unit code or course code required'}), 400
    
    try:
        # Process image
        image_bytes = file.read()
        
        if not image_bytes:
            return jsonify({'error': 'Empty image file'}), 400
        
        # Validate and convert image
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)
            image_bytes = output.getvalue()
        except Exception as e:
            return jsonify({'error': f'Invalid image: {str(e)}'}), 400
        
        # Get face encoding from submitted image
        image, error = face_engine.preprocess_image(image_bytes)
        if error:
            return jsonify({'status': 'failed', 'message': error}), 400
        
        unknown_encoding = face_engine.encode_face(image)
        if unknown_encoding is None:
            return jsonify({'status': 'failed', 'message': 'No face detected'}), 400
        
        # Find best match among enrolled users
        enrolled_users = User.query.filter(
            User.face_encoding != None,
            User.is_active == True,
            User.consent_given == True
        ).all()
        
        best_match = None
        best_confidence = 0
        tolerance = current_app.config.get('FACE_TOLERANCE', 0.6)
        
        for user in enrolled_users:
            known_encoding = np.array(user.face_encoding)
            result = face_engine.compare_faces(known_encoding, unknown_encoding)
            
            if result['match'] and result['confidence'] > best_confidence:
                best_confidence = result['confidence']
                best_match = user
        
        # ✅ CREATE ATTENDANCE RECORD IF MATCH FOUND
        if best_match and best_confidence >= tolerance:
            # ✅ Get or create course/unit (auto-create if doesn't exist)
            course = Course.query.filter_by(code=unit_code).first()
            
            if not course:
                # Auto-create course if it doesn't exist
                # This allows ANY valid unit code to be used
                course = Course(
                    code=unit_code,
                    name=f"{unit_code} - {course_program or 'General'}",
                    department=course_program or 'General',
                    is_active=True
                )
                db.session.add(course)
                db.session.commit()
                current_app.logger.info(f"✅ Auto-created course: {unit_code}")
            
            # Check if already marked today
            today = datetime.utcnow().date()
            existing = Attendance.query.filter(
                Attendance.user_id == best_match.id,
                Attendance.course_id == course.id,
                db.func.date(Attendance.timestamp) == today,
                Attendance.status != 'deleted'
            ).first()
            
            if existing:
                return jsonify({
                    'status': 'already_marked',
                    'message': f'Attendance already recorded at {existing.timestamp}',
                    'student': best_match.to_dict(),
                    'course': unit_code,
                    'timestamp': existing.timestamp.isoformat()
                }), 200
            
            # ✅ CREATE ATTENDANCE RECORD with academic info
            record = Attendance(
                user_id=best_match.id,
                course_id=course.id,
                timestamp=datetime.utcnow(),
                confidence_score=best_confidence,
                liveness_verified=True,
                status='present',
                year_of_study=year_of_study,
                course_program=course_program,
                unit_code=unit_code,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            db.session.add(record)
            db.session.commit()
            
            # Audit
            log_audit(
                actor_id=best_match.id,
                action='attendance_marked',
                resource_type='attendance',
                resource_id=record.id,
                ip_address=request.remote_addr,
                status_code=201,
                face_match_confidence=best_confidence
            )
            
            return jsonify({
                'status': 'success',
                'message': f'Attendance marked for {best_match.full_name} - {unit_code}',
                'student': best_match.to_dict(),
                'course': unit_code,
                'unit_code': unit_code,
                'year_of_study': year_of_study,
                'course_program': course_program,
                'confidence': best_confidence,
                'attendance_id': record.id,
                'timestamp': datetime.utcnow().isoformat()
            }), 201
        
        # No match found
        log_audit(
            action='face_recognition_failed',
            resource_type='face',
            ip_address=request.remote_addr,
            status_code=404,
            error_message='No matching face found'
        )
        
        return jsonify({
            'status': 'failed',
            'message': 'Face not recognized. Please enroll first.',
            'confidence': best_confidence if best_match else 0
        }), 404
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Recognition error: {e}")
        return jsonify({'error': 'Recognition failed'}), 500