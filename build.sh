#!/usr/bin/env bash
# الخروج عند الخطأ
set -o errexit

# تثبيت التبعيات
pip install -r requirements.txt

# جمع الملفات الثابتة
python manage.py collectstatic --no-input

# تطبيق هجرات قاعدة البيانات
python manage.py migrate

