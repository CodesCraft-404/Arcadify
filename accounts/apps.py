from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()

        if not User.objects.filter(gmail="admin@gmail.com").exists():
            User.objects.create_superuser(
                gmail="admin@gmail.com",
                name="Admin",
                gamer_name="admin",
                age=21,
                password="admin123"
            )