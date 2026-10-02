from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension


class Migration(migrations.Migration):

    dependencies = [
        ('Products', '0001_initial'),  # apki asal pehli migration ka naam yahan confirm kar lena
    ]

    operations = [
        TrigramExtension(),
    ]