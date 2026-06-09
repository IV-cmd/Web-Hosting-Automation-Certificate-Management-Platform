import subprocess
import docker
from kubernetes import client, config
from app import db, socketio
from app.models.deployment import Deployment, DeploymentStatus
from app.models.application import Application
from app.utils.vault_client import VaultClient

class DeploymentService:
    def __init__(self):
        self.vault_client = VaultClient()
        try:
            config.load_kube_config()
            self.k8s_apps = client.AppsV1Api()
            self.k8s_core = client.CoreV1Api()
        except:
            self.k8s_apps = None
            self.k8s_core = None
        
        self.docker_client = docker.from_env()
    
    def deploy(self, deployment_id):
        """Execute blue-green deployment"""
        deployment = Deployment.query.get(deployment_id)
        if not deployment:
            raise Exception("Deployment not found")
        
        application = Application.query.get(deployment.application_id)
        
        try:
            deployment.status = DeploymentStatus.BUILDING
            db.session.commit()
            self._emit_status(deployment_id, 'Building Docker image')
            
            # Build Docker image
            image_tag = f"{application.name}:{deployment.version}"
            self._build_docker_image(application.repository_url, image_tag)
            
            deployment.status = DeploymentStatus.DEPLOYING_GREEN
            db.session.commit()
            self._emit_status(deployment_id, 'Deploying to green environment')
            
            # Deploy to green environment
            green_deployment_name = f"{application.name}-green"
            self._deploy_to_kubernetes(application, green_deployment_name, image_tag)
            deployment.green_environment = green_deployment_name
            
            # Wait for green to be healthy
            if self._wait_for_deployment_ready(green_deployment_name):
                deployment.status = DeploymentStatus.SWITCHING
                db.session.commit()
                self._emit_status(deployment_id, 'Switching traffic to green')
                
                # Switch traffic
                self._switch_traffic(application.name, green_deployment_name)
                deployment.active_environment = green_deployment_name
                deployment.status = DeploymentStatus.SUCCESS
                deployment.completed_at = datetime.utcnow()
                
                # Update application status
                application.status = ApplicationStatus.DEPLOYED
                application.docker_image = image_tag
                
                db.session.commit()
                self._emit_status(deployment_id, 'Deployment successful')
            else:
                raise Exception("Green environment failed to become healthy")
                
        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            deployment.completed_at = datetime.utcnow()
            application.status = ApplicationStatus.FAILED
            db.session.commit()
            self._emit_status(deployment_id, f'Deployment failed: {str(e)}')
            
            # Auto rollback
            if deployment.blue_environment:
                self.rollback(deployment_id)
    
    def rollback(self, deployment_id):
        """Rollback to previous deployment"""
        deployment = Deployment.query.get(deployment_id)
        if not deployment:
            raise Exception("Deployment not found")
        
        application = Application.query.get(deployment.application_id)
        
        try:
            if deployment.blue_environment:
                self._switch_traffic(application.name, deployment.blue_environment)
                deployment.active_environment = deployment.blue_environment
                deployment.status = DeploymentStatus.ROLLED_BACK
                db.session.commit()
                self._emit_status(deployment_id, 'Rollback successful')
        except Exception as e:
            deployment.error_message = str(e)
            db.session.commit()
            self._emit_status(deployment_id, f'Rollback failed: {str(e)}')
            raise e
    
    def _build_docker_image(self, repo_url, image_tag):
        """Build Docker image from repository"""
        # Clone repository
        subprocess.run(['git', 'clone', repo_url, '/tmp/build'], check=True)
        
        # Build image
        self.docker_client.images.build(
            path='/tmp/build',
            tag=image_tag
        )
        
        # Push to registry (if configured)
        # self.docker_client.images.push(image_tag)
    
    def _deploy_to_kubernetes(self, application, deployment_name, image_tag):
        """Deploy to Kubernetes using Helm charts"""
        if not self.k8s_apps:
            raise Exception("Kubernetes client not configured")
        
        # Get secrets from Vault
        secrets = self.vault_client.get_secrets(application.name)
        
        # Create deployment manifest
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name=deployment_name),
            spec=client.V1DeploymentSpec(
                replicas=2,
                selector=client.V1LabelSelector(
                    match_labels={'app': application.name}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={'app': application.name, 'env': deployment_name}
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=application.name,
                                image=image_tag,
                                ports=[client.V1ContainerPort(container_port=application.port)],
                                env=[
                                    client.V1EnvVar(
                                        name=key,
                                        value=value
                                    )
                                    for key, value in application.environment.items()
                                ]
                            )
                        ]
                    )
                )
            )
        )
        
        namespace = 'default'
        self.k8s_apps.create_namespaced_deployment(namespace, deployment)
    
    def _wait_for_deployment_ready(self, deployment_name, timeout=300):
        """Wait for deployment to be ready"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            deployment = self.k8s_apps.read_namespaced_deployment(
                deployment_name, 'default'
            )
            
            if deployment.status.ready_replicas == deployment.spec.replicas:
                return True
            
            time.sleep(5)
        
        return False
    
    def _switch_traffic(self, app_name, target_deployment):
        """Switch traffic using Kubernetes service"""
        # Update service selector to point to new deployment
        service = self.k8s_core.read_namespaced_service(app_name, 'default')
        service.spec.selector = {'env': target_deployment}
        self.k8s_core.patch_namespaced_service(app_name, 'default', service)
    
    def _emit_status(self, deployment_id, message):
        """Emit deployment status via WebSocket"""
        socketio.emit('deployment_status', {
            'deployment_id': deployment_id,
            'message': message
        })
    
    def get_logs(self, deployment_id):
        """Get deployment logs"""
        deployment = Deployment.query.get(deployment_id)
        if not deployment:
            raise Exception("Deployment not found")
        
        # Get logs from Kubernetes pods
        pods = self.k8s_core.list_namespaced_pod(
            'default',
            label_selector=f'env={deployment.active_environment}'
        )
        
        logs = []
        for pod in pods.items:
            try:
                pod_logs = self.k8s_core.read_namespaced_pod_log(
                    pod.metadata.name,
                    'default'
                )
                logs.append({
                    'pod': pod.metadata.name,
                    'logs': pod_logs
                })
            except:
                pass
        
        return logs
