from app import db
from datetime import datetime
from enum import Enum

class DeploymentStatus(Enum):
    PENDING = 'pending'
    BUILDING = 'building'
    DEPLOYING_BLUE = 'deploying_blue'
    DEPLOYING_GREEN = 'deploying_green'
    SWITCHING = 'switching'
    SUCCESS = 'success'
    FAILED = 'failed'
    ROLLED_BACK = 'rolled_back'

class DeploymentStrategy(Enum):
    BLUE_GREEN = 'blue_green'
    ROLLING = 'rolling'

class Deployment(db.Model):
    __tablename__ = 'deployments'
    
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(50), nullable=False)
    commit_hash = db.Column(db.String(100))
    status = db.Column(db.Enum(DeploymentStatus), default=DeploymentStatus.PENDING)
    strategy = db.Column(db.Enum(DeploymentStrategy), default=DeploymentStrategy.BLUE_GREEN)
    blue_environment = db.Column(db.String(50))
    green_environment = db.Column(db.String(50))
    active_environment = db.Column(db.String(50))
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Foreign keys
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'version': self.version,
            'commit_hash': self.commit_hash,
            'status': self.status.value,
            'strategy': self.strategy.value,
            'blue_environment': self.blue_environment,
            'green_environment': self.green_environment,
            'active_environment': self.active_environment,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'application_id': self.application_id
        }
