import os
from datetime import datetime

import pytz
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/requests.db?check_same_thread=False'
app.config['SECRET_KEY'] = 'ugyuvhjbguyfucgvhjyftycgvhhoijpjiugiytydrtyfyguihoj'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the app
db = SQLAlchemy(app)

# Georgian timezone
GEORGIA_TIMEZONE = pytz.timezone('Asia/Tbilisi')


# Define the model
class HelpRequest(db.Model):
    __tablename__ = 'help_requests'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    contact = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    message = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.String, nullable=False)
    ip_address = db.Column(db.String, nullable=False)

    def as_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'contact': self.contact,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'message': self.message,
            'timestamp': self.timestamp,
            'ip_address': self.ip_address
        }


# Initialize the database
def init_db():
    with app.app_context():
        try:
            db.create_all()  # Create tables based on models
            print("Database initialized successfully")
        except Exception as e:
            print(f"Database initialization failed: {e}")


# Initialize the database when the app starts


@app.route('/')
def index():
    """Home page with map for submitting help requests"""
    return render_template('index.html')


@app.route('/submit_request', methods=['POST'])
def submit_request():
    """Submit a new help request"""
    name = request.form.get('name')
    contact = request.form.get('contact')
    location = request.form.get('location')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    message = request.form.get('message')

    if not all([name, contact, location, latitude, longitude, message]):
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    now = datetime.now(GEORGIA_TIMEZONE)
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    ip_address = request.remote_addr

    try:
        new_request = HelpRequest(name=name, contact=contact, location=location,
                                  latitude=latitude, longitude=longitude,
                                  message=message, timestamp=timestamp, ip_address=ip_address)
        db.session.add(new_request)
        db.session.commit()
        return jsonify({"status": "success", "message": "Help request submitted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Database error: {e}"}), 500


@app.route('/requests')
def view_requests():
    """Page to view all help requests"""
    return render_template('requests.html')


@app.route('/delete_request/<int:request_id>', methods=['DELETE'])
def delete_request(request_id):
    """Delete a help request (only if the IP matches)"""
    ip_address = request.remote_addr

    try:
        request_to_delete = HelpRequest.query.filter_by(id=request_id, ip_address=ip_address).first()
        if request_to_delete:
            db.session.delete(request_to_delete)
            db.session.commit()
            return jsonify({"status": "success", "message": "Request deleted successfully"})
        else:
            return jsonify({"status": "error", "message": "Request not found or not authorized to delete"}), 403
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Database error: {e}"}), 500


@app.route('/api/requests')
def get_requests():
    """API endpoint to get all help requests"""
    try:
        requests = HelpRequest.query.all()  # Fetch all help requests
        return jsonify([request.as_dict() for request in requests])  # Convert each to a dict
    except Exception as e:
        return jsonify({"status": "error", "message": f"Database error: {e}"}), 500


@app.route('/health')
def health_check():
    """Simple health check route"""
    return jsonify({"status": "ok", "message": "App is running!"})


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
