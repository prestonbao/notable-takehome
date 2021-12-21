from flask import Flask, request, jsonify, json
from datetime import datetime
from jsonschema import validate

app = Flask(__name__)

@app.route('/', methods=['GET'])
def welcome():
    return "Notable API Homepage"

@app.route('/doctors/', methods=['GET'])
# This method will return all doctors in memory in the format
def get_doctors():
    with open('./doctors.txt', 'r') as f:
        data = f.read()
        return data

@app.route('/appointments/<int:doctor_id>/<string:date>/', methods=["GET"])
# This method will return all appointments for doctor with @doctor_id on @date
# @param: doctor_id - unique ID for particular doctor
# @param: date - particular date must be in format YYYY-MM-DD
def get_appointments_for_doctor_on_day(doctor_id, date):
    if not date:
        return "Missing date parameter", 400
    elif not validate_date(date):
        return "Incorrect date format, needs to be YYYY-MM-DD", 400
    elif not check_if_doctor_exists(doctor_id):
        return "Doctor {} does not exist".format(doctor_id), 400

    appointments = []
    with open('./appointments.txt', 'r') as f:
        data = f.read()
        records = json.loads(data)
        for appointment in records:
            if appointment['date'] == date and appointment['doctor_id'] == doctor_id:
                appointments.append(appointment)
    
    if not appointments:
        return "No appointments found for doctor {} on {} ".format(str(doctor_id), date)
    else:
        return jsonify(appointments)

@app.route('/appointments/<int:doctor_id>/', methods=["DELETE"])
# This method will delete an appointment for doctor with @doctor_id with appointment_id == @appointment_id
# @param: doctor_id - unique ID for particular doctor
# @param: appointment_id - unique appointment id
def delete_appointment_for_doctor_on_day(doctor_id):
    if not check_if_doctor_exists(doctor_id):
        return "Doctor {} does not exist".format(doctor_id), 400

    appointment_id = request.args.get('appointment_id')

    updated_appointments = []
    with open('./appointments.txt', 'r') as f:
        data = f.read()
        records = json.loads(data)
        deleted = {}
        for appointment in records:
            if int(appointment['id']) == int(appointment_id):
                deleted = appointment
                continue
            updated_appointments.append(appointment)
    
    with open('./appointments.txt', 'w') as f:
        f.write(json.dumps(updated_appointments, indent=2))
    
    if deleted:
        return "Appointment for {} {} on {} has been deleted.".format(deleted['first_name'], deleted['last_name'], deleted['date'])
    else:
        return "No appointment found."

@app.route('/appointments/<int:doctor_id>/', methods=["POST"])
# This method will create an appointment for doctor with @doctor_id
# @param: doctor_id - unique ID for particular doctor
def create_appointment(doctor_id):
    new_appointment = json.loads(request.data)
    if not validate_appointment_data(new_appointment):
        return "Invalid appointment data format", 400
    if not check_if_doctor_exists(doctor_id):
        return "Doctor {} does not exist".format(doctor_id), 400

    time = new_appointment['time']
    if not validate_time(time):
        return "Invalid time or time format", 400

    current_appointments = get_appointments_for_doctor_on_day(doctor_id, new_appointment['date'])
    if type(current_appointments) != str:
        if not validate_appointment_count(current_appointments.json, time):
            return "Doctor has too many appointments at this time {}".format(time), 400

    appointments = []
    with open('./appointments.txt', 'r') as f:
        data = f.read()
        if not data:
            appointments = [new_appointment]
        else:
            appointments = json.loads(data)
            appointments.append(new_appointment)

    with open('./appointments.txt', 'w') as f:
        f.write(json.dumps(appointments, indent=2))
    
    return jsonify(new_appointment)
     
def validate_date(date_string):
    try:
        if date_string != datetime.strptime(date_string, "%Y-%m-%d").strftime('%Y-%m-%d'):
            raise ValueError("Incorrect date format, needs to be YYYY-MM-DD")
        return True
    except:
        return False

def check_if_doctor_exists(doctor_id):
    data = json.loads(get_doctors())
    for doctor in data:
        if doctor['id'] == doctor_id:
            return True
    return False

def validate_appointment_data(new_appointment):
    schema = {
        "type" : "object",
        "properties" : {
            "id" : {"type" : "number"},
            "first_name" : {"type" : "string"},
            "last_name" : {"type" : "string"},
            "date" : {"type" : "string"},
            "doctor_id": {"type": "number"},
            "new_patient" : {"type" : "boolean"},
            "time" : {"type" : "string"},
        }
    }
    try:
        validate(instance=new_appointment, schema=schema)
        return True
    except:
        return False

def validate_time(time_string):
    if time_string != datetime.strptime(time_string, "%H:%M").strftime('%H:%M'):
            raise ValueError("Incorrect date format, needs to be HH:MM")
    minutes = time_string.split(':')[1]
    if minutes not in ['00', '15', '30', '45']:
        return False
    else:
        return True

def validate_appointment_count(current_appointments, time):
    count = 0
    for appointment in current_appointments:
        if appointment['time'] == time:
            count += 1
        if count >= 3:
            return False
    return True

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=105, debug=True)