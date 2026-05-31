from app import db
from datetime import datetime
from enum import Enum

class CertificateType(Enum):
    SINGLE = 'single'
    WILDCARD = 'wildcard'
    MULTI_DOMAIN = 'multi_domain'

class CertificateStatus(Enum):
    PENDING = 'pending'
    ISSUED = 'issued'
    RENEWING = 'renewing'
    EXPIRED = 'expired'
    REVOKED = 'revoked'

class Certificate(db.Model):
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False)
    certificate_type = db.Column(db.Enum(CertificateType), default=CertificateType.WILDCARD)
    status = db.Column(db.Enum(CertificateStatus), default=CertificateStatus.PENDING)
    cert_path = db.Column(db.String(500))
    key_path = db.Column(db.String(500))
    issued_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    auto_renew = db.Column(db.Boolean, default=True)
    renew_days_before = db.Column(db.Integer, default=30)
    web_server = db.Column(db.String(50))  # nginx, apache
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'domain': self.domain,
            'certificate_type': self.certificate_type.value,
            'status': self.status.value,
            'cert_path': self.cert_path,
            'key_path': self.key_path,
            'issued_at': self.issued_at.isoformat() if self.issued_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'auto_renew': self.auto_renew,
            'renew_days_before': self.renew_days_before,
            'web_server': self.web_server,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
