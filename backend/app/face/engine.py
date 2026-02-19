"""Face recognition engine with privacy-by-design"""
import os
import numpy as np
import face_recognition
from PIL import Image
from io import BytesIO
from ..config import Config


class FaceEngine:
    """Encapsulates face recognition operations"""
    
    def __init__(self, tolerance=None, model=None):
        self.tolerance = tolerance or Config.FACE_TOLERANCE
        self.model = model or Config.FACE_ENCODING_MODEL
    
    def load_image(self, image_data):
        """Load image from bytes or file path"""
        if isinstance(image_data, bytes):
            return face_recognition.load_image_file(BytesIO(image_data))
        return face_recognition.load_image_file(image_data)
    
    def detect_faces(self, image):
        """Detect face locations in image"""
        return face_recognition.face_locations(image, model=self.model)
    
    def encode_face(self, image, face_location=None):
        """Generate 128-d encoding vector for a face"""
        encodings = face_recognition.face_encodings(
            image, 
            known_face_locations=[face_location] if face_location else None,
            num_jitters=1  # Balance speed/accuracy
        )
        return encodings[0] if encodings else None
    
    def compare_faces(self, known_encoding, unknown_encoding, tolerance=None):
        """Compare two face encodings"""
        tol = tolerance or self.tolerance
        matches = face_recognition.compare_faces(
            [known_encoding], 
            unknown_encoding, 
            tolerance=tol
        )
        distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
        return {
            'match': matches[0],
            'confidence': 1 - distance,  # Convert distance to confidence
            'distance': distance
        }
    
    def validate_image_quality(self, image, min_face_size=80):
        """Basic quality checks before processing"""
        faces = self.detect_faces(image)
        
        if not faces:
            return {'valid': False, 'error': 'No face detected'}
        
        if len(faces) > 1:
            return {'valid': False, 'error': 'Multiple faces detected'}
        
        # Check face size
        top, right, bottom, left = faces[0]
        face_width = right - left
        face_height = bottom - top
        
        if face_width < min_face_size or face_height < min_face_size:
            return {'valid': False, 'error': 'Face too small'}
        
        return {
            'valid': True,
            'face_location': faces[0],
            'dimensions': {'width': face_width, 'height': face_height}
        }
    
    def preprocess_image(self, image_bytes, max_size_mb=5):
        """Preprocess image: validate size, format, orientation"""
        # Check file size
        if len(image_bytes) > max_size_mb * 1024 * 1024:
            return None, 'Image too large'
        
        # Load and validate
        try:
            img = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Auto-orient based on EXIF
            from PIL.ExifTags import TAGS, GPSTAGS
            try:
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break
                exif = img._getexif()
                if exif and orientation in exif:
                    if exif[orientation] == 3:
                        img = img.rotate(180, expand=True)
                    elif exif[orientation] == 6:
                        img = img.rotate(270, expand=True)
                    elif exif[orientation] == 8:
                        img = img.rotate(90, expand=True)
            except:
                pass  # Skip if no EXIF
            
            # Convert back to bytes for face_recognition
            output = BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)
            
            return face_recognition.load_image_file(output), None
            
        except Exception as e:
            return None, f'Image processing error: {str(e)}'