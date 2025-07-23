To install and run the project!

```bash
    # Clone the repository
    git clone <your-repo-url>

    # Make sure directory is right project folder (where manage.py is)
    cd /myprojects/smerp/

    # venv (preferred)
    python -m venv .venv
    source .venv/bin/activate

    # Install Python dependencies
    pip install -r requirements.txt

    # Create the .env file
    touch .env

    # Generate a Django secret key
    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
__info__:
**paste the django secret key and database credentials to .env** 
i use postgres, requirements.txt includes postgres adapter
if you use another SQL based db install its library first.
make sure to change 'ENGINE' value from the dev.py and prod.py in __/config/settings/__ !
use django documentation for accepted values.

example .env
```env
SECRET_KEY=your-generated-secret-key
POSTGRES_DB=your_db_name
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

after that run migrations from terminal, before that check db connection
```bash
python manage.py dbshell
python manage.py migrate
```

if any problems occur just delete migrations and cache, you can use below
```bash
find . -path '*/migrations/*.py' -not -name '__init__.py' -delete
find . -type d -name '__pycache__' -exec rm -rf {} +

#run migrations again
python manage.py makemigrations
python manage.py migrate

python manage.py runserver
```
start the project and we are good to go!
you can see the api discovery by typing
/redoc/ or /swagger/ at the end of the url from browser





