from sqlalchemy import create_engine, Column, Integer, String, Date, Numeric, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func # Para las funciones de fecha/hora de la DB
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy() #Inicializa SQLAlchemy sin la aplicación

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    identification_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc))
    # Relación con TumorMeasurement
    measurements = db.relationship(
        'TumorMeasurement', 
        backref='patient', 
        lazy=True, 
        order_by="TumorMeasurement.measurement_date")

    def __repr__(self):
        return f"<Patient {self.name} ({self.identification_number})>"

class TumorMeasurement(db.Model):
    __tablename__ = 'tumor_measurements'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    size_cm3 = db.Column(db.Float, nullable=False)
    measurement_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text) #para comentarios adiciionales

    def __repr__(self):
        return f"<TumorMeasurement PatientID:{self.patient_id} Size:{self.size_cm3}cm³ Date:{self.measurement_date}>"

def init_db(app):
    with app.app_context():
        db.create_all()
