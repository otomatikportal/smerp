# Django Localization Setup and Workflow for Windows

## Installing Localization Tools on Windows

### 1. Install GNU gettext tools
- Download the complete gettext package for Windows from [https://mlocati.github.io/articles/gettext-iconv-windows.html](https://mlocati.github.io/articles/gettext-iconv-windows.html)
- Choose the appropriate version (32-bit or 64-bit) with "shared" flavor
- Install the package and ensure all development tools are included (`msgfmt`, `msguniq`, `xgettext`, etc.)

### 2. Verify Installation
```cmd
gettext --version
msgfmt --version
msguniq --version
xgettext --version
```

### 3. Add to PATH (if needed)
- Add the gettext bin directory (e.g., `C:\Program Files\gettext-iconv\bin`) to your Windows PATH environment variable
- Restart your terminal/IDE after making PATH changes

## Django Project Setup

### 1. Configure Settings
```python
# settings.py
LANGUAGE_CODE = 'tr'  # Your default language
USE_I18N = True
USE_L10N = True

# Supported languages
LANGUAGES = [
    ('tr', 'Türkçe'),
    ('en', 'English'),
]

# Locale paths
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),  # Your custom translations
]
```

### 2. Ensure Middleware is Configured
```python
# settings.py
MIDDLEWARE = [
    # ... other middleware
    'django.middleware.locale.LocaleMiddleware', # put locale before common !
    'django.middleware.common.CommonMiddleware', 
    # ... rest of middleware
]
```

## Development Workflow for Custom Messages

### Phase 1: Development in Primary Language (Turkish)

1. **Write translatable strings in your code**:
```python
# In models, views, serializers, etc.
from django.utils.translation import gettext_lazy as _

class MyModel(models.Model):
    name = models.CharField(_("Ad"), max_length=100)
    description = models.TextField(_("Açıklama"), blank=True)
```

2. **Extract translatable strings**:
```bash
python manage.py makemessages -l en
```
This creates `locale/en/LC_MESSAGES/django.po`

3. **Translate strings** in the generated `.po` file:
```po
#: core/models.py:10
msgid "Ad"
msgstr "Name"

#: core/models.py:11
msgid "Açıklama"
msgstr "Description"
```

4. **Compile translations**:
```bash
python manage.py compilemessages
```

### Phase 2: Ongoing Development

1. **Add new translatable strings** to your code in Turkish
2. **Update message files**:
```bash
python manage.py makemessages -l en
```
3. **Translate new entries** in the `.po` file
4. **Recompile**:
```bash
python manage.py compilemessages
```

### Directory Structure
```
your_project/
├── locale/
│   ├── tr/
│   │   └── LC_MESSAGES/
│   │       ├── django.po  # Turkish source strings
│   │       └── django.mo  # Compiled Turkish (optional for primary language)
│   └── en/
│       └── LC_MESSAGES/
│           ├── django.po  # English translations
│           └── django.mo  # Compiled English translations
├── manage.py
└── settings.py
```

## Testing Translations

### Create a Test View
```python
from django.utils.translation import gettext as _
from rest_framework.views import APIView
from rest_framework.response import Response

class TranslationTestView(APIView):
    def get(self, request):
        test_translations = {
            'current_language': str(request.LANGUAGE_CODE),
            'test_string': _('Ad'),
        }
        return Response(test_translations)
```

### Key Commands Summary
```bash
# Extract new/updated translatable strings
python manage.py makemessages -l [language_code]

# Compile translations for use
python manage.py compilemessages

# Clear cache and restart server if needed
# Remove __pycache__ directories and restart Django server
```

This workflow allows you to develop primarily in Turkish while maintaining a clear path to add English (or other language) translations as needed.