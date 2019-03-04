# Generated by Django 2.0 on 2019-03-04 11:49

import accounts.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('entm', '0001_initial'),
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='MyUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('user_name', models.CharField(max_length=30, unique=True, verbose_name='用户名')),
                ('real_name', models.CharField(blank=True, max_length=30, verbose_name='真实姓名')),
                ('sex', models.CharField(blank=True, max_length=30, verbose_name='性别')),
                ('phone_number', models.CharField(blank=True, max_length=30, verbose_name='手机')),
                ('expire_date', models.CharField(blank=True, max_length=30, verbose_name='授权截止日期')),
                ('idstr', models.CharField(blank=True, max_length=300, null=True)),
                ('uuid', models.CharField(blank=True, max_length=300, null=True)),
                ('email', models.EmailField(blank=True, max_length=255, verbose_name='邮箱')),
                ('is_active', models.BooleanField(default=True, verbose_name='启停状态')),
                ('staff', models.BooleanField(default=False)),
                ('admin', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MyRoles',
            fields=[
                ('group_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='auth.Group')),
                ('notes', models.CharField(blank=True, max_length=156)),
                ('rid', models.CharField(blank=True, max_length=1000)),
                ('uid', models.CharField(blank=True, max_length=100)),
                ('permissionTree', models.TextField(blank=True)),
                ('belongto', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='roles', to='entm.Organization')),
            ],
            bases=('auth.group',),
            managers=[
                ('objects', accounts.models.MyRolesManager()),
            ],
        ),
        migrations.AddField(
            model_name='myuser',
            name='Role',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='users', to='accounts.MyRoles', verbose_name='角色'),
        ),
        migrations.AddField(
            model_name='myuser',
            name='belongto',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='users', to='entm.Organization', verbose_name='所属组织'),
        ),
        migrations.AddField(
            model_name='myuser',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='myuser',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
    ]
