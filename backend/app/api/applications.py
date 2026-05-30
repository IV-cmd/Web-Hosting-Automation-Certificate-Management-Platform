from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.application import Application, ApplicationStatus

applications_bp = Blueprint('applications', __name__)

@applications_bp.route('/', methods=['GET'])
@jwt_required()
def get_applications():
    user_id = get_jwt_identity()
    applications = Application.query.filter_by(user_id=user_id).all()
    return jsonify({'applications': [a.to_dict() for a in applications]}), 200

@applications_bp.route('/', methods=['POST'])
@jwt_required()
def create_application():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    application = Application(
        name=data['name'],
        repository_url=data['repository_url'],
        branch=data.get('branch', 'main'),
        port=data.get('port', 80),
        environment=data.get('environment', {}),
        user_id=user_id
    )
    
    db.session.add(application)
    db.session.commit()
    
    return jsonify({'application': application.to_dict()}), 201

@applications_bp.route('/<int:application_id>', methods=['GET'])
@jwt_required()
def get_application(application_id):
    application = Application.query.get_or_404(application_id)
    return jsonify({'application': application.to_dict()}), 200

@applications_bp.route('/<int:application_id>', methods=['PUT'])
@jwt_required()
def update_application(application_id):
    application = Application.query.get_or_404(application_id)
    data = request.get_json()
    
    application.name = data.get('name', application.name)
    application.repository_url = data.get('repository_url', application.repository_url)
    application.branch = data.get('branch', application.branch)
    application.port = data.get('port', application.port)
    application.environment = data.get('environment', application.environment)
    
    db.session.commit()
    
    return jsonify({'application': application.to_dict()}), 200

@applications_bp.route('/<int:application_id>', methods=['DELETE'])
@jwt_required()
def delete_application(application_id):
    application = Application.query.get_or_404(application_id)
    db.session.delete(application)
    db.session.commit()
    
    return jsonify({'message': 'Application deleted successfully'}), 200
