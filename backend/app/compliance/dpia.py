"""Data Protection Impact Assessment helpers"""
from datetime import datetime


class DPIAChecklist:
    """Helper for Kenya Data Protection Act 2019 compliance"""
    
    REQUIRED_CONSENT_FIELDS = [
        'biometric_processing',
        'data_storage', 
        'purpose_limitation'
    ]
    
    @staticmethod
    def validate_consent(consent_data):
        """Check if consent meets legal requirements"""
        issues = []
        
        for field in DPIAChecklist.REQUIRED_CONSENT_FIELDS:
            if field not in consent_data:
                issues.append(f'Missing consent field: {field}')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }