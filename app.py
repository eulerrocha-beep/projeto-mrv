from datetime import date, datetime
from html import escape
import re

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///barbearia.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JSON_SORT_KEYS"] = False
db = SQLAlchemy(app)


class Service(db.Model):
    __tablename__ = "services"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)


class Appointment(db.Model):
    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(5), nullable=False)
    customer_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    service = db.relationship("Service")
    __table_args__ = (UniqueConstraint("date", "time", name="uq_appointment_slot"),)


AVAILABLE_TIMES = ["09:00", "10:00", "11:30", "14:00", "15:30", "17:00", "18:30"]
PHONE_PATTERN = re.compile(r"^\(?\d{2}\)?\s?\d{5}-?\d{4}$")


def clean_text(value, limit):
    if not isinstance(value, str):
        return ""
    return escape(re.sub(r"\s+", " ", value).strip()[:limit])


def normalize_phone(value):
    if not isinstance(value, str):
        return ""
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    return ""


def seed_services():
    if Service.query.count() == 0:
        db.session.add_all([
            Service(name="Corte Clássico", price=45.00, duration=30),
            Service(name="Barba Completa", price=35.00, duration=30),
            Service(name="Combo Corte + Barba", price=70.00, duration=60),
        ])
        db.session.commit()


with app.app_context():
    db.create_all()
    seed_services()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/agendar")
def schedule_page():
    return render_template("index.html")


@app.route("/sucesso")
def success_page():
    return render_template("index.html")


@app.route("/api/servicos")
def get_services():
    services = Service.query.order_by(Service.id).all()
    return jsonify([{"id": s.id, "nome": s.name, "preco": s.price, "duracao": s.duration} for s in services])


@app.route("/api/agendamentos", methods=["GET"])
def get_occupied_slots():
    selected_date = request.args.get("data", "")
    try:
        parsed = datetime.strptime(selected_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Data inválida. Use o formato YYYY-MM-DD."}), 400
    if parsed < date.today():
        return jsonify({"error": "Não é possível consultar datas passadas."}), 400
    occupied = [row.time for row in Appointment.query.filter_by(date=selected_date).all()]
    available = [time for time in AVAILABLE_TIMES if time not in occupied]
    return jsonify({"ocupados": occupied, "disponiveis": available})


@app.route("/api/agendamentos", methods=["POST"])
def create_appointment():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Corpo da solicitação inválido."}), 400

    service_id = data.get("service_id")
    selected_date = data.get("data")
    selected_time = data.get("hora")
    name = clean_text(data.get("nome", ""), 120)
    phone = normalize_phone(data.get("telefone", ""))

    name_parts = name.split()
    if len(name_parts) < 2 or len(name) < 5 or not re.search(r"[A-Za-zÀ-ÿ]", name):
        return jsonify({"error": "Informe seu nome completo."}), 400
    if not re.fullmatch(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s.'-]*", name):
        return jsonify({"error": "O nome contém caracteres inválidos."}), 400
    if not phone:
        return jsonify({"error": "Informe um telefone válido com DDD."}), 400

    try:
        parsed_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        if parsed_date < date.today():
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Selecione uma data válida."}), 400

    if selected_time not in AVAILABLE_TIMES:
        return jsonify({"error": "Horário inválido."}), 400

    service = db.session.get(Service, service_id) if isinstance(service_id, int) else None
    if not service:
        return jsonify({"error": "Serviço inválido."}), 400

    try:
        appointment = Appointment(service_id=service.id, date=selected_date, time=selected_time,
                                  customer_name=name, phone=phone)
        db.session.add(appointment)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Este horário acabou de ser reservado. Escolha outro horário."}), 409
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erro ao salvar agendamento."}), 500

    return jsonify({
        "id": appointment.id,
        "servico": service.name,
        "preco": service.price,
        "duracao": service.duration,
        "data": appointment.date,
        "hora": appointment.time,
        "nome": appointment.customer_name,
        "telefone": appointment.phone
    }), 201


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
