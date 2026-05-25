from django.db import models

# Create your models here.
class People(models.Model):
    """
    人物名
    """
    name = models.CharField(max_length=30,verbose_name="人物名")
    description = models.TextField(verbose_name="役職",null=True,blank=True)

    class Meta:
        db_table = "People_people"