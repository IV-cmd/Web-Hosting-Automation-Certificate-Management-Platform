import subprocess
import os
from datetime import datetime, timedelta
from app import db
from app.models.certificate import Certificate, CertificateStatus
from app.utils.vault_client import VaultClient

class CertificateService:
    def __init__(self):
        self.vault_client = VaultClient()
    
    def provision_certificate(self, certificate_id):
        """Provision SSL certificate using Let's Encrypt"""
        certificate = Certificate.query.get(certificate_id)
        if not certificate:
            raise Exception("Certificate not found")
        
        certificate.status = CertificateStatus.PENDING
        db.session.commit()
        
        try:
            # Use certbot to obtain certificate
            cmd = [
                'certbot',
                'certonly',
                '--non-interactive',
                '--agree-tos',
                '--email', 'admin@' + certificate.domain,
                '--domain', certificate.domain,
                '--webroot',
                '--webroot-path', '/var/www/certbot'
            ]
            
            if certificate.certificate_type.value == 'wildcard':
                cmd.extend([
                    '--domain', '*.' + certificate.domain,
                    '--manual',
                    '--preferred-challenges', 'dns'
                ])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Certbot failed: {result.stderr}")
            
            # Store certificate paths
            certificate.cert_path = f"/etc/letsencrypt/live/{certificate.domain}/fullchain.pem"
            certificate.key_path = f"/etc/letsencrypt/live/{certificate.domain}/privkey.pem"
            certificate.issued_at = datetime.utcnow()
            certificate.expires_at = datetime.utcnow() + timedelta(days=90)
            certificate.status = CertificateStatus.ISSUED
            
            # Store credentials in Vault
            self.vault_client.store_certificate(
                certificate.domain,
                certificate.cert_path,
                certificate.key_path
            )
            
            db.session.commit()
            
            # Configure web server
            self._configure_web_server(certificate)
            
        except Exception as e:
            certificate.status = CertificateStatus.FAILED
            db.session.commit()
            raise e
    
    def renew_certificate(self, certificate_id):
        """Renew SSL certificate"""
        certificate = Certificate.query.get(certificate_id)
        if not certificate:
            raise Exception("Certificate not found")
        
        certificate.status = CertificateStatus.RENEWING
        db.session.commit()
        
        try:
            cmd = [
                'certbot',
                'renew',
                '--non-interactive',
                '--cert-name', certificate.domain
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Certificate renewal failed: {result.stderr}")
            
            certificate.issued_at = datetime.utcnow()
            certificate.expires_at = datetime.utcnow() + timedelta(days=90)
            certificate.status = CertificateStatus.ISSUED
            
            db.session.commit()
            
            # Reload web server
            self._reload_web_server(certificate)
            
        except Exception as e:
            certificate.status = CertificateStatus.FAILED
            db.session.commit()
            raise e
    
    def revoke_certificate(self, certificate_id):
        """Revoke SSL certificate"""
        certificate = Certificate.query.get(certificate_id)
        if not certificate:
            raise Exception("Certificate not found")
        
        cmd = [
            'certbot',
            'revoke',
            '--non-interactive',
            '--cert-path', certificate.cert_path
        ]
        
        subprocess.run(cmd, capture_output=True, text=True)
        
        certificate.status = CertificateStatus.REVOKED
        db.session.commit()
    
    def _configure_web_server(self, certificate):
        """Configure Nginx or Apache with SSL certificate"""
        if certificate.web_server == 'nginx':
            self._configure_nginx(certificate)
        elif certificate.web_server == 'apache':
            self._configure_apache(certificate)
    
    def _configure_nginx(self, certificate):
        """Configure Nginx with SSL certificate"""
        # Implementation would generate Nginx config
        pass
    
    def _configure_apache(self, certificate):
        """Configure Apache with SSL certificate"""
        # Implementation would generate Apache config
        pass
    
    def _reload_web_server(self, certificate):
        """Reload web server to apply new certificate"""
        if certificate.web_server == 'nginx':
            subprocess.run(['nginx', '-s', 'reload'])
        elif certificate.web_server == 'apache':
            subprocess.run(['systemctl', 'reload', 'apache2'])
    
    def check_expiring_certificates(self):
        """Check for certificates expiring soon and trigger renewal"""
        certificates = Certificate.query.filter_by(auto_renew=True).all()
        
        for cert in certificates:
            if cert.expires_at:
                days_until_expiry = (cert.expires_at - datetime.utcnow()).days
                if days_until_expiry <= cert.renew_days_before:
                    self.renew_certificate(cert.id)
