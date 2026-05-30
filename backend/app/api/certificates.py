from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.certificate import Certificate, CertificateType, CertificateStatus
from app.services.certificate_service import CertificateService

certificates_bp = Blueprint('certificates', __name__)
cert_service = CertificateService()

@certificates_bp.route('/', methods=['GET'])
@jwt_required()
def get_certificates():
    certificates = Certificate.query.all()
    return jsonify({'certificates': [c.to_dict() for c in certificates]}), 200

@certificates_bp.route('/', methods=['POST'])
@jwt_required()
def create_certificate():
    data = request.get_json()
    
    certificate = Certificate(
        domain=data['domain'],
        certificate_type=CertificateType(data.get('certificate_type', 'wildcard')),
        web_server=data.get('web_server', 'nginx'),
        auto_renew=data.get('auto_renew', True),
        renew_days_before=data.get('renew_days_before', 30)
    )
    
    db.session.add(certificate)
    db.session.commit()
    
    # Trigger certificate provisioning
    try:
        cert_service.provision_certificate(certificate.id)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify({'certificate': certificate.to_dict()}), 201

@certificates_bp.route('/<int:certificate_id>', methods=['GET'])
@jwt_required()
def get_certificate(certificate_id):
    certificate = Certificate.query.get_or_404(certificate_id)
    return jsonify({'certificate': certificate.to_dict()}), 200

@certificates_bp.route('/<int:certificate_id>/renew', methods=['POST'])
@jwt_required()
def renew_certificate(certificate_id):
    certificate = Certificate.query.get_or_404(certificate_id)
    
    try:
        cert_service.renew_certificate(certificate_id)
        return jsonify({'message': 'Certificate renewal initiated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@certificates_bp.route('/<int:certificate_id>', methods=['DELETE'])
@jwt_required()
def delete_certificate(certificate_id):
    certificate = Certificate.query.get_or_404(certificate_id)
    
    try:
        cert_service.revoke_certificate(certificate_id)
        db.session.delete(certificate)
        db.session.commit()
        return jsonify({'message': 'Certificate deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
