from django.apps import AppConfig


class ProcurementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'procurement'

    def ready(self):
        from django.db.models.signals import post_migrate
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        from procurement.models import ProcurementOrder
        import procurement.signals
        
        def create_default_groups(sender, **kwargs):
            # Define groups and their procurement permissions
            base_perms = [
                'add_procurementorder',
                'change_procurementorder',
                'view_procurementorder',
            ]
            groups_permissions = {
                'Procurement Officer': base_perms + [
                    'submit_procurementorder',
                    'cancel_procurementorder'
                ],
                'Procurement Manager': base_perms + [
                    'approve_procurementorder',
                    'reject_procurementorder',
                ],
                'Accountant': base_perms + [
                    'bill_procurementorder',
                    'cancel_procurementorder',
                    'reject_procurementorder'
                ],
            }
            ct = ContentType.objects.get_for_model(ProcurementOrder)
            for group_name, perms in groups_permissions.items():
                group, _ = Group.objects.get_or_create(name=group_name)
                for perm_codename in perms:
                    perm = Permission.objects.filter(content_type=ct, codename=perm_codename).first()
                    if perm:
                        group.permissions.add(perm)
            # Groups are additive: if a group exists, permissions are added, not overwritten

        post_migrate.connect(create_default_groups, sender=self)
