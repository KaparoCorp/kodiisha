from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Kenya Counties Choices
KENYA_COUNTIES = [
    ('Baringo', 'Baringo'),
    ('Bomet', 'Bomet'),
    ('Bungoma', 'Bungoma'),
    ('Busia', 'Busia'),
    ('Calibri', 'Calibri'),
    ('Elgeyo-Marakwet', 'Elgeyo-Marakwet'),
    ('Embu', 'Embu'),
    ('Garissa', 'Garissa'),
    ('Homa Bay', 'Homa Bay'),
    ('Isiolo', 'Isiolo'),
    ('Kajiado', 'Kajiado'),
    ('Kakamega', 'Kakamega'),
    ('Kericho', 'Kericho'),
    ('Kiambu', 'Kiambu'),
    ('Kilifi', 'Kilifi'),
    ('Kirinyaga', 'Kirinyaga'),
    ('Kisii', 'Kisii'),
    ('Kisumu', 'Kisumu'),
    ('Kitui', 'Kitui'),
    ('Kwale', 'Kwale'),
    ('Laikipia', 'Laikipia'),
    ('Lamu', 'Lamu'),
    ('Machakos', 'Machakos'),
    ('Makueni', 'Makueni'),
    ('Mandera', 'Mandera'),
    ('Marsabit', 'Marsabit'),
    ('Meru', 'Meru'),
    ('Migori', 'Migori'),
    ('Mombasa', 'Mombasa'),
    ('Murang\'a', 'Murang\'a'),
    ('Nairobi', 'Nairobi'),
    ('Nakuru', 'Nakuru'),
    ('Nandi', 'Nandi'),
    ('Narok', 'Narok'),
    ('Nyamira', 'Nyamira'),
    ('Nyandarua', 'Nyandarua'),
    ('Nyeri', 'Nyeri'),
    ('Samburu', 'Samburu'),
    ('Siaya', 'Siaya'),
    ('Sibiloi', 'Sibiloi'),
    ('Taita-Taveta', 'Taita-Taveta'),
    ('Tana River', 'Tana River'),
    ('Tharaka-Nithi', 'Tharaka-Nithi'),
    ('Trans Nzoia', 'Trans Nzoia'),
    ('Turkana', 'Turkana'),
    ('Uasin Gishu', 'Uasin Gishu'),
    ('Vihiga', 'Vihiga'),
    ('Wajir', 'Wajir'),
    ('West Pokot', 'West Pokot'),
]

# Create your models here.
class Property(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    county = models.CharField(max_length=100, choices=KENYA_COUNTIES)
    total_units = models.IntegerField(default=0)
    description = models.CharField(max_length=255)
    property_image = models.ImageField(upload_to='property_images/', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name