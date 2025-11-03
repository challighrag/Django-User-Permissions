from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Permission
from django.contrib.auth.models import BaseUserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _
import binascii
import os
import secrets
from django.conf import settings
# from .managers import CustomUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(max_length=150, unique=False, blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, ** kwargs):
    if created:
        Token.objects.create(user=instance)

class Task(models.Model):
    # Many tasks /User
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"User: {self.user.first_name}, Task: {self.title}, Description: {self.description}"

# class Token(models.Model):
#     # One token /User
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='token')
#     key = models.CharField(max_length=64, unique=True,default= binascii.hexlify(os.urandom(20)).decode())
#     permissions = models.ManyToManyField(Permission, blank=True)

#     def __str__(self):
#         return f"Token for {self.user.first_name}: {self.key}"


class Token(models.Model):
    """
    The default authorization token model.
    """
    key = models.CharField(_("Key"), max_length=40, primary_key=True, default= secrets.token_hex(20))
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE, verbose_name=_("User")
    )
    created = models.DateTimeField(_("Created"), auto_now_add=True)


    class Meta:
        # Work around for a bug in Django:
        # https://code.djangoproject.com/ticket/19422
        #
        # Also see corresponding ticket:
        # https://github.com/encode/django-rest-framework/issues/705
        # abstract = 'rest_framework.authtoken' not in settings.INSTALLED_APPS
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")

    def save(self, *args, **kwargs):
        """
        Save the token instance.

        If no key is provided, generates a cryptographically secure key.
        For new tokens, ensures they are inserted as new (not updated).
        """
        if not self.key:
            self.key = self.generate_key()
            # For new objects, force INSERT to prevent overwriting existing tokens
            if self._state.adding:
                kwargs['force_insert'] = True
        return super().save(*args, **kwargs)

    @classmethod
    def generate_key(cls):
        return secrets.token_hex(20)

    def __str__(self):
        return self.key