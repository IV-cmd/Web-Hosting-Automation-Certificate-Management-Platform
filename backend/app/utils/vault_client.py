import hvac
import os
from dotenv import load_dotenv

load_dotenv()

class VaultClient:
    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv('VAULT_ADDR', 'http://localhost:8200'),
            token=os.getenv('VAULT_TOKEN', 'dev-token')
        )
        
        # Enable KV secrets engine if not enabled
        try:
            self.client.secrets.kv.v2.create_secret_engine(
                path='secret',
                mount_point='secret'
            )
        except:
            pass
    
    def store_secret(self, path, secret_data):
        """Store secret in Vault"""
        self.client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret=secret_data,
            mount_point='secret'
        )
    
    def get_secret(self, path):
        """Retrieve secret from Vault"""
        response = self.client.secrets.kv.v2.read_secret_version(
            path=path,
            mount_point='secret'
        )
        return response['data']['data']
    
    def delete_secret(self, path):
        """Delete secret from Vault"""
        self.client.secrets.kv.v2.delete_metadata_and_all_versions(
            path=path,
            mount_point='secret'
        )
    
    def store_certificate(self, domain, cert_path, key_path):
        """Store SSL certificate in Vault"""
        with open(cert_path, 'r') as f:
            cert_content = f.read()
        
        with open(key_path, 'r') as f:
            key_content = f.read()
        
        secret_data = {
            'certificate': cert_content,
            'private_key': key_content
        }
        
        self.store_secret(f'certificates/{domain}', secret_data)
    
    def get_certificate(self, domain):
        """Retrieve SSL certificate from Vault"""
        return self.get_secret(f'certificates/{domain}')
    
    def get_secrets(self, app_name):
        """Get all secrets for an application"""
        try:
            return self.get_secret(f'applications/{app_name}')
        except:
            return {}
