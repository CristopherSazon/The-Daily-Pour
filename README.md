# The Daily Pour

A café site for browsing the menu and placing a pickup order. A chat barista recommends drinks from the catalog and remembers a guest’s usual.

The visual reference is [the-daily-pour-tau.vercel.app](https://the-daily-pour-tau.vercel.app/).

## Apps

| App | What it owns |
| --- | --- |
| `apps.menu` | Categories, products, the homepage, and the full menu |
| `apps.orders` | The pickup bag and saved orders |
| `apps.ai.barista` | The Groq barista and guest preferences |

Pages share `templates/base.html`. Shared markup is in `templates/components/`. Each app has its own template folder. Styles, scripts, and photos are in `static/menu/`.

Business rules live in each app’s `services.py`. Views stay thin.

## Run it

Python 3.12 and PostgreSQL. Create a database and role that match `.env`, then:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Fill `POSTGRES_PASSWORD` and `GROQ_API_KEY` in `.env`. `BARISTA_MODEL` defaults to `openai/gpt-oss-20b`. Settings load `.env` only when a variable is missing, so restart the server after changing it.

Migrations load the menu fixture. Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## Pages

| Path | Purpose |
| --- | --- |
| `/` | Homepage and featured drinks |
| `/menu/` | Full catalog, search, product dialog, order bag, barista |
| `POST /orders/` | Save a pickup order |
| `/barista/` | Barista chat |
| `/admin/` | Django admin |

The bag asks for a name, phone, and pickup window. After a successful order the empty state reads “We'll have it ready for pickup.”

The barista replies through Groq and only names products that exist. Django sets the price and saves the order. The guest taps Add, then Place your order. With no `GROQ_API_KEY`, the chat says the barista is away.

## Tests

```bash
python manage.py test apps.menu apps.orders apps.ai.barista
```
