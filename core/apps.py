from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from django.db.models.signals import post_migrate
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        from core.models import Material, Contact, Company

        def create_default_groups(sender, **kwargs):
            base_perms_material = [
                'add_material',
                'change_material',
                'view_material',
            ]

            base_perms_contact = [
                'add_contact',
                'change_contact',
                'view_contact',
            ]

            base_perms_company = [
                'add_company',
                'change_company',
                'view_company',
            ]

            groups_permissions = {
                'Material Manager': base_perms_material,
                'Material Observer': ['view_material'],
                'Contact Manager': base_perms_contact,
                'Contact Observer': ['view_contact'],
                'Company Manager': base_perms_company,
                'Company Observer': ['view_company'],
            }

            ct_material = ContentType.objects.get_for_model(Material)
            ct_contact = ContentType.objects.get_for_model(Contact)
            ct_company = ContentType.objects.get_for_model(Company)

            for group_name, perms in groups_permissions.items():
                group, _ = Group.objects.get_or_create(name=group_name)
                for perm_codename in perms:
                    if 'material' in perm_codename:
                        perm = Permission.objects.filter(content_type=ct_material, codename=perm_codename).first()
                    elif 'contact' in perm_codename:
                        perm = Permission.objects.filter(content_type=ct_contact, codename=perm_codename).first()
                    elif 'company' in perm_codename:
                        perm = Permission.objects.filter(content_type=ct_company, codename=perm_codename).first()
                    else:
                        perm = None
                    if perm:
                        group.permissions.add(perm)
            # Groups are additive: if a group exists, permissions are added, not overwritten

        post_migrate.connect(create_default_groups, sender=self)
