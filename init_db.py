from app import app, db, Service, seed_services

with app.app_context():
    db.drop_all()
    db.create_all()
    seed_services()
    print("Banco barbearia.db criado e serviços cadastrados.")
