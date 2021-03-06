# Generated by Django 2.0 on 2019-03-04 11:49

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300, null=True, verbose_name='组织机构名称')),
                ('attribute', models.CharField(blank=True, max_length=300, null=True, verbose_name='组织机构性质')),
                ('register_date', models.CharField(blank=True, max_length=30, null=True, verbose_name='注册日期')),
                ('owner_name', models.CharField(blank=True, max_length=300, null=True, verbose_name='负责人')),
                ('phone_number', models.CharField(blank=True, max_length=300, null=True, verbose_name='电话号码')),
                ('firm_address', models.CharField(blank=True, max_length=300, null=True, verbose_name='地址')),
                ('organlevel', models.CharField(blank=True, max_length=30, null=True, verbose_name='Level')),
                ('coorType', models.CharField(blank=True, max_length=30, null=True)),
                ('longitude', models.CharField(blank=True, max_length=30, null=True)),
                ('latitude', models.CharField(blank=True, max_length=30, null=True)),
                ('zoomIn', models.CharField(blank=True, max_length=30, null=True)),
                ('islocation', models.CharField(blank=True, max_length=30, null=True)),
                ('location', models.CharField(blank=True, max_length=30, null=True)),
                ('province', models.CharField(blank=True, max_length=30, null=True)),
                ('city', models.CharField(blank=True, max_length=30, null=True)),
                ('district', models.CharField(blank=True, max_length=30, null=True)),
                ('cid', models.CharField(blank=True, max_length=300, null=True)),
                ('pId', models.CharField(blank=True, max_length=300, null=True)),
                ('is_org', models.BooleanField(max_length=300)),
                ('uuid', models.CharField(blank=True, max_length=300, null=True)),
                ('adcode', models.CharField(blank=True, max_length=300, null=True)),
                ('districtlevel', models.CharField(blank=True, max_length=300, null=True)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='entm.Organization')),
            ],
            options={
                'db_table': 'dma_organization',
                'managed': True,
            },
        ),
    ]
