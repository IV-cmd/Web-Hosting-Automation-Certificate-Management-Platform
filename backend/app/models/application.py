from app import db
from datetime import datetime
from enum import Enum

class ApplicationStatus(Enum):
    CREATED = 'created'
    DEPLOYING = 'deploying'
    DEPLOYED = 'deployed'
    FAILED = 'failed'
    STOPPED = 'stopped'

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    repository_url = db.Column(db.String(255), nullable=False)
    branch = db.Column(db.String(50), default='main')
    docker_image = db.Column(db.String(255))
    port = db.Column(db.Integer, default=80)
    environment = db.Column(db.JSON, default={})
    status = db.Column(db.Enum(ApplicationStatus), default=ApplicationStatus.CREATED)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    certificate_id = db.Column(db.Integer, db.ForeignKey('certificates.id'), nullable=True)
    
    # Relationships
    deployments = db.relationship('Deployment', backref='application', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'repository_url': self.repository_url,
            'branch': self.branch,
            'docker_image': self.docker_image,
            'port': self.port,
            'environment': self.environment,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user_id': self.user_id,
            'certificate_id': self.certificate_id
        }
