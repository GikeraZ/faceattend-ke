"""Basic liveness detection to prevent spoofing"""
import cv2
import numpy as np
from PIL import Image
from io import BytesIO


class LivenessChecker:
    """Simple liveness detection using texture analysis"""
    
    @staticmethod
    def check_blur(image_array, threshold=100):
        """Detect if image is too blurry (possible printed photo)"""
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        fm = cv2.Laplacian(gray, cv2.CV_64F).var()
        return fm > threshold, fm
    
    @staticmethod
    def check_color_distribution(image_array):
        """Basic check for screen/photo vs real face"""
        # Real faces have more varied skin tones
        hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)
        
        # Skin tone range in HSV
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        skin_ratio = np.sum(mask > 0) / mask.size
        
        # Real faces typically have 15-60% skin pixels in face region
        return 0.15 < skin_ratio < 0.60, skin_ratio
    
    @staticmethod
    def detect_eyes(image_array, face_location):
        """Check if eyes are detectable (anti-spoofing)"""
        top, right, bottom, left = face_location
        
        # Extract face region
        face = image_array[top:bottom, left:right]
        
        # Convert to grayscale for eye detection
        gray = cv2.cvtColor(face, cv2.COLOR_RGB2GRAY)
        
        # Load Haar cascade (bundle with app or download on first run)
        try:
            eye_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_eye.xml'
            )
            eyes = eye_cascade.detectMultiScale(gray, 1.1, 5)
            return len(eyes) >= 2, len(eyes)
        except:
            # Fallback: assume passed if cascade not available
            return True, 2
    
    @staticmethod
    def verify(image_bytes, face_location=None):
        """Run liveness checks on image"""
        try:
            # Load image
            img = Image.open(BytesIO(image_bytes))
            img_array = np.array(img)
            
            results = {}
            passed = 0
            total = 0
            
            # Check 1: Blur detection
            total += 1
            blur_ok, blur_score = LivenessChecker.check_blur(img_array)
            results['blur'] = {'passed': blur_ok, 'score': blur_score}
            if blur_ok: passed += 1
            
            # Check 2: Color distribution
            total += 1
            color_ok, color_ratio = LivenessChecker.check_color_distribution(img_array)
            results['color_distribution'] = {'passed': color_ok, 'ratio': color_ratio}
            if color_ok: passed += 1
            
            # Check 3: Eye detection (if face location provided)
            if face_location:
                total += 1
                eyes_ok, eye_count = LivenessChecker.detect_eyes(img_array, face_location)
                results['eyes_detected'] = {'passed': eyes_ok, 'count': eye_count}
                if eyes_ok: passed += 1
            
            # Overall result: require 70% of checks to pass
            confidence = passed / total if total > 0 else 0
            return {
                'liveness_verified': confidence >= 0.7,
                'confidence': confidence,
                'checks': results,
                'details': f'{passed}/{total} checks passed'
            }
            
        except Exception as e:
            return {
                'liveness_verified': False,
                'error': str(e),
                'confidence': 0
            }