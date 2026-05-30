from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, socketio
from app.models.deployment import Deployment, DeploymentStatus, DeploymentStrategy
from app.models.application import Application
from app.services.deployment_service import DeploymentService

deployments_bp = Blueprint('deployments', __name__)
deployment_service = DeploymentService()

@deployments_bp.route('/', methods=['GET'])
@jwt_required()
def get_deployments():
    application_id = request.args.get('application_id')
    query = Deployment.query
    
    if application_id:
        query = query.filter_by(application_id=application_id)
    
    deployments = query.order_by(Deployment.started_at.desc()).all()
    return jsonify({'deployments': [d.to_dict() for d in deployments]}), 200

@deployments_bp.route('/', methods=['POST'])
@jwt_required()
def create_deployment():
    data = request.get_json()
    
    application = Application.query.get_or_404(data['application_id'])
    
    deployment = Deployment(
        version=data['version'],
        commit_hash=data.get('commit_hash'),
        strategy=DeploymentStrategy(data.get('strategy', 'blue_green')),
        application_id=data['application_id']
    )
    
    db.session.add(deployment)
    db.session.commit()
    
    # Trigger deployment in background
    deployment_service.deploy(deployment.id)
    
    return jsonify({'deployment': deployment.to_dict()}), 201

@deployments_bp.route('/<int:deployment_id>', methods=['GET'])
@jwt_required()
def get_deployment(deployment_id):
    deployment = Deployment.query.get_or_404(deployment_id)
    return jsonify({'deployment': deployment.to_dict()}), 200

@deployments_bp.route('/<int:deployment_id>/rollback', methods=['POST'])
@jwt_required()
def rollback_deployment(deployment_id):
    deployment = Deployment.query.get_or_404(deployment_id)
    
    try:
        deployment_service.rollback(deployment_id)
        return jsonify({'message': 'Rollback initiated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@deployments_bp.route('/<int:deployment_id>/logs', methods=['GET'])
@jwt_required()
def get_deployment_logs(deployment_id):
    deployment = Deployment.query.get_or_404(deployment_id)
    logs = deployment_service.get_logs(deployment_id)
    return jsonify({'logs': logs}), 200
