from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'

    def ready(self):
        from django.db.models.signals import post_migrate
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        from inventory.models import InventoryLocation, StockRecord

        def create_default_groups(sender, **kwargs):
            base_perms_inventory_location = [
                'add_inventorylocation',
                'change_inventorylocation',
                'view_inventorylocation',
            ]
            base_perms_stock_record = [
                'add_stockrecord',
                'change_stockrecord',
                'view_stockrecord',
            ]
            groups_permissions = {
                'Inventory Location Manager': (base_perms_inventory_location, InventoryLocation),
                'Inventory Location Observer': (['view_inventorylocation'], InventoryLocation),
                'Stock Record Manager': (base_perms_stock_record, StockRecord),
                'Stock Record Observer': (['view_stockrecord'], StockRecord),
            }
            for group_name, (perms, model) in groups_permissions.items():
                ct = ContentType.objects.get_for_model(model)
                group, _ = Group.objects.get_or_create(name=group_name)
                for perm_codename in perms:
                    perm = Permission.objects.filter(content_type=ct, codename=perm_codename).first()
                    if perm:
                        group.permissions.add(perm)
            # Groups are additive: if a group exists, permissions are added, not overwritten

        post_migrate.connect(create_default_groups, sender=self)
