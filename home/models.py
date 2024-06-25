from django.db import models

# Create your models here.
class Menu(models.Model):
    TYPES = [('veg', 'veg only'),
             ('non_veg', 'non-veg only'),
             ('egg', 'contains egg')]
    
    item = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.IntegerField()
    category = models.ManyToManyField('category', related_name='item', blank=True)
    veg_nonveg_egg = models.CharField(max_length=10, choices=TYPES, default='veg')
    avg_time_taken = models.IntegerField(null=True)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.item}'
    


class Category(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, null=True, blank=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    def __str__(self):
        return f'{self.name}'