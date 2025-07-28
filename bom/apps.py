from django.apps import AppConfig


class BomConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bom'
    
    def ready(self):
        import bom.signals
