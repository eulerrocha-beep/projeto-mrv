# Le Nilson Barber

Sistema mobile-first de agendamento sem login, desenvolvido com Flask, SQLite, HTML, CSS e JavaScript.

## Estrutura

- `app.py` — aplicação, modelos SQLAlchemy e API REST
- `init_db.py` — recria o banco e realiza o seed dos serviços
- `templates/index.html` — telas do fluxo
- `static/styles.css` — identidade visual responsiva
- `static/app.js` — navegação e integração assíncrona
- `tests/test_app.py` — testes de API e concorrência

## Instalação no Windows

```powershell
cd "c:\Users\euler\OneDrive\Desktop\Todos projetos\projeto mrv"
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python init_db.py
python app.py
```

Acesse `http://127.0.0.1:5000`.

## Testes

```powershell
pytest -q
```

Os testes validam catálogo, criação de reserva, conflito HTTP 409, telefone inválido e ocupação de horários.

## API

- `GET /api/servicos`
- `GET /api/agendamentos?data=YYYY-MM-DD`
- `POST /api/agendamentos`

Exemplo de corpo JSON:

```json
{
  "service_id": 1,
  "data": "2026-11-20",
  "hora": "09:00",
  "nome": "João Silva",
  "telefone": "11999999999"
}
```

O banco usa restrição UNIQUE em `(date, time)`, impedindo dois agendamentos no mesmo dia e horário.
