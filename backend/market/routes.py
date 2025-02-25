from flask_cors import cross_origin
from flask_mail import Mail, Message
import re
from flask import flash, json, session
from flask_session import Session
from market import app
from flask import render_template, request, jsonify
from market.CreateMeet.create_event import createEvent
from market.models import Patients, Doctor, Prescription, past_history_of_illness, immunisation
from market import db
from flask_login import login_user
#from market.processor import chatbot_response
# from processor import chatbot_response
# imports for PyJWT authentication
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask import Response
from flask_cors import cross_origin


# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = "gydbybuduubchydbbu46t363vydw3u6y88hbb2"
jwt = JWTManager(app)

mail = Mail(app)  # instantiate the mail class
tokenDict={}
doctorDict={}
currentDict={}

#Call for ChatBot Form
# @app.route('/index', methods=["GET", "POST"])
# @cross_origin()
# def index():
#     return render_template('index.html', **locals())

# Chatbot
# @app.route('/chatbot', methods=["GET", "POST"])
# @cross_origin()
# def chatbotResponse():

#     if request.method == 'POST':
#         the_question = request.form['question']

#         response = chatbot_response(the_question)

#     return jsonify({"response": response})


# User Login
@app.route("/api/login", methods=['POST'])
@cross_origin()
def login():
    username = request.json['username']
    password = request.json['password']
    if username == "":
        result = {
            "status": "unsuccessful",
            "message": "Enter username"
        }
        return jsonify(result), 401

    if password == "":
        result = {
            "status": "unsuccessful",
            "message": "Enter Password"
        }
        return jsonify(result), 401

    attempted_user = Patients.query.filter_by(username=username).first()
    if attempted_user and attempted_user.password_hash == password:
        access_token = create_access_token(identity=username)
        session['token'] = access_token
        tokenDict[attempted_user.id]=access_token
        result = {
            "status": "successful",
            "username": username,
            "message": "Login Successful",
            "access_token":access_token,
            "id":attempted_user.id
        }
        print(tokenDict)
        return jsonify(result), 200
    else:
        result = {
            "status": "unsuccessful",
            "message": "Invalid Credentials"
        }
        return jsonify(result), 401

# User Logout
@app.route('/api/logout/<int:user_id>',methods=["GET"])
@cross_origin()
def logout_page(user_id):
    del tokenDict[user_id]
    print(tokenDict)
    result={
        "status":"Logged out"
    }
    return jsonify(result),200

# Doctor Login
@app.route('/api/doctor', methods=['POST'])
@cross_origin()
def doctor():
    email_address=request.json['email_address']
    attempted_doctor = Doctor.query.filter_by(email_address=email_address).first()
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if(not re.fullmatch(regex, request.json['email_address'])):
        result={
        "status":"unsuccessful",
        "email_address":email_address,
        "message":"Invalid Email"
        }  
        return jsonify(result),422
    elif attempted_doctor is None:
        result={
        "status":"unsuccessful",
        "email_address":email_address,
        "message":"Invalid Credentials"
        }  
        return jsonify(result),401
    
    else:
        password=request.json['password']
        if attempted_doctor.password_hash==password:
            access_token = create_access_token(identity=email_address)
            session['doctorToken']=access_token
            doctorDict[attempted_doctor.id]=access_token
            result={
                "email_address":email_address,
                "status":"successful",
                "id":attempted_doctor.id,
                "token":access_token
            }
            currentDict['current']=attempted_doctor.id
            return jsonify(result),200
        else:
            result={
                "status":"unsuccessful",
                "message":"Invalid Password"
            }
            return jsonify(result),401

# Doctor Logout
@app.route('/api/logoutDoctor/<int:user_id>',methods=["GET"])
@cross_origin()
def Doctorlogout_page(user_id):
    del doctorDict[user_id]
    del currentDict["current"]
    print(doctorDict)
    result={
        "status":"Logged out"
    }
    return jsonify(result),200

# User Register
@app.route('/api/register', methods=['POST'])
@cross_origin()
def register():
    username = request.json['username']
    attempted_user = Patients.query.filter_by(username=username).first()
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    regexpass = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    email_address = request.json['email_address']
    if(not re.fullmatch(regex, request.json['email_address'])):
        result = {
            "status": "unsuccessful",
            "email_address": email_address,
            "message": "Invalid Email"
        }
        return jsonify(result), 422
    if attempted_user is not None:
        result = {
            "status": "unsuccessful",
            "email_address": email_address,
            "message": "User already exists"
        }
        return jsonify(result), 409
    if(not re.fullmatch(regexpass, request.json['password'])):
        result = {
            "status": "unsuccessful",
            "email_address": email_address,
            "message": "Invalid Password"
        }
        return jsonify(result), 422
    else:
        password = request.json['password']
        fullname = request.json['fullname']
        user_to_create = Patients(fullname, email_address, password, username)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        result = {
            "status": "successful",
            "username": username
        }
        return jsonify(result), 201

# Doctor Select User 
@app.route('/api/doctor/users', methods=['GET', 'POST'])
@cross_origin()
def testin():
    frontToken = str(request.headers.get('x-access-token'))
    if doctorDict[currentDict['current']]==frontToken:
        patients = Patients.query
        patientsJson = json.dumps([r.as_dict() for r in patients])
        return patientsJson, 200
    result={
        "status":"unsuccessful",
        "message":"Token Not Passed"
    }
    return jsonify(result), 401

# User GET Prescription
@app.route("/api/prescribe/<int:pid>", methods=["GET"])
@cross_origin()
def get_prescription(pid):
    frontToken = str(request.headers.get('x-access-token'))
    if request.method == "GET" and tokenDict[pid]!=frontToken:
        result={
        "status":"unsuccessful",
        "message":"Invalid Token"
        }
        return jsonify(result), 401
        
    prescriptions = Prescription.query.filter_by(userID=pid)
    s = json.dumps([r.as_dict() for r in prescriptions])
    return s, 200



# Doctor POST Prescription
@app.route("/api/doctor/prescribe/<int:user_id>", methods=["POST"])
@cross_origin()
def add_prescription(user_id):
    frontToken = str(request.headers.get('x-access-token'))
    if request.method == 'POST' and doctorDict[currentDict['current']]==frontToken:
        prescriptionID = request.json['pi']
        medItem = request.json['Medication item']
        prepSubstanceName = request.json['Name']
        prepForm = request.json['Form']
        prepStrength = request.json['strength']
        prepStrengthUnit = request.json['strengthUnit']
        diluentAmount = request.json['numerator']
        diluentUnit = request.json['numeratorUnit']
        ingredientSubstanceName = request.json['substanceName']
        ingredientForm = request.json['ingredientForm']
        ingredientCategory = request.json['category']
        ingredientStrength = request.json['ingredientstrength']
        ingredientStrengthUnit = request.json['strengthUnit']
        ingredientDescription = request.json['medicationDescription']
        ingredientAmount = request.json['ingredient-amount']
        ingredientAmountUnit = request.json['ingredient-amountUnit']
        ingredientRole = request.json['roleStatus']
        ingredientRole2 = request.json['role']
        medDescription = request.json['description']
        medRoute = request.json['route']
        medDosageInstructions = request.json['dosageInstructions']
        doseAmount = request.json['doseAmount']
        doseAmountLower = request.json['doseAmountLower']
        doseAmountUpper = request.json['doseAmountUpper']
        doseUnit = request.json['doseUnit']
        doseTimingFreq = request.json['frequency']
        doseTimingFreqUnit = request.json['frequencyUnit']
        doseTimingFreqLower = request.json['frequencyLower']
        doseTimingFreqLowerUnit = request.json['frequencyLowerUnit']
        doseTimingFreqUpper = request.json['frequencyUpper']
        doseTimingFreqUpperUnit = request.json['frequencyUpperUnit']
        doseTimingInterval = request.json['interval']
        doseSpecificTime = request.json['st']
        doseNamedTimeEvent = request.json['nte']
        doseNamedTimeEvent2 = request.json['nte2']
        doseExactTimingCritical = request.json['timeCritical']
        doseAsRequired = request.json['asRequired']
        doseAsRequiredCriterion = request.json['requiredcriterion']
        infusionAdminRateQ = request.json['iar']
        infusionAdminRateUnit = request.json['iarUnit']
        infusionAdminRateT = request.json['iar1']
        doseAdminDuration = request.json['administration']
        doseDirectionDuration1 = request.json['directionDuration']
        doseDirectionDuration2 = request.json['directionDuration2']
        directionRepetitionInterval = request.json['repetitionInterval']
        directionSpecificDate = request.json['specificDate']
        directionSpecificTime = request.json['specificTime']
        directionSpecificDoW = request.json['specificDayofweek']
        directionSpecificDoM = request.json['specificdayofmonth']
        directionEventName = request.json['eventName']
        directionEventStartInterval = request.json['eventStartInterval']
        safetyMaxAmount = request.json['maximumAmount']
        safetyMaxAmountUnit = request.json['maximumAmountDoseUnit']
        safetyAllowedPeriod = request.json['allowedPeriod']
        overrideReason = request.json['overrideReason']
        orderAdditionalInstructions = request.json['additionalInstructions']
        orderReason = request.json['reason']
        courseStatus = request.json['status']
        courseDiscontinuedDate = request.json['dateDiscontinued']
        courseDiscontinuedTime = request.json['timeDiscontinued']
        courseWrittenDate = request.json['dateWritten']
        courseWrittenTime = request.json['timeWritten']
        authNumberofRepeatsAllowed = request.json['nora']
        authValidityPeriodDate = request.json['validityPeriod']
        authValidityPeriodTime = request.json['validityPeriodTime']
        dispenseInstruction = request.json['dispenseInstructions']
        dispenseAmountDescription = request.json['amountDescription']
        dispenseAmount = request.json['amountindispense']
        dispenseAmountUnits = request.json['dispenseUnits']
        dispenseDurationofSupply = request.json['dos']
        orderComment = request.json['comment']
        orderID = request.json['identifier']
        userID = user_id
        prescription = Prescription(prescriptionID=prescriptionID, medItem=medItem, prepSubstanceName=prepSubstanceName, prepForm=prepForm, prepStrength=prepStrength, prepStrengthUnit=prepStrengthUnit, diluentAmount=diluentAmount, diluentUnit=diluentUnit, ingredientSubstanceName=ingredientSubstanceName, ingredientForm=ingredientForm, ingredientCategory=ingredientCategory, ingredientStrength=ingredientStrength, ingredientStrengthUnit=ingredientStrengthUnit, ingredientDescription=ingredientDescription, ingredientAmount=ingredientAmount, ingredientAmountUnit=ingredientAmountUnit, ingredientRole=ingredientRole, ingredientRole2=ingredientRole2, medDescription=medDescription, medRoute=medRoute, medDosageInstructions=medDosageInstructions, doseAmount=doseAmount, doseAmountLower=doseAmountLower, doseAmountUpper=doseAmountUpper, doseNamedTimeEvent2=doseNamedTimeEvent2, doseUnit=doseUnit, doseTimingFreq=doseTimingFreq, doseTimingFreqUnit=doseTimingFreqUnit, doseTimingFreqLower=doseTimingFreqLower, doseTimingFreqLowerUnit=doseTimingFreqLowerUnit, doseTimingFreqUpper=doseTimingFreqUpper, doseTimingFreqUpperUnit=doseTimingFreqUpperUnit, doseTimingInterval=doseTimingInterval, doseSpecificTime=doseSpecificTime, doseNamedTimeEvent=doseNamedTimeEvent, doseExactTimingCritical=doseExactTimingCritical, doseAsRequired=doseAsRequired, doseAsRequiredCriterion=doseAsRequiredCriterion, infusionAdminRateQ=infusionAdminRateQ,
                                    infusionAdminRateUnit=infusionAdminRateUnit, infusionAdminRateT=infusionAdminRateT, doseAdminDuration=doseAdminDuration, doseDirectionDuration1=doseDirectionDuration1, doseDirectionDuration2=doseDirectionDuration2, directionRepetitionInterval=directionRepetitionInterval, directionSpecificDate=directionSpecificDate, directionSpecificTime=directionSpecificTime, directionSpecificDoW=directionSpecificDoW, directionSpecificDoM=directionSpecificDoM, directionEventName=directionEventName, directionEventStartInterval=directionEventStartInterval, safetyMaxAmount=safetyMaxAmount, safetyMaxAmountUnit=safetyMaxAmountUnit, safetyAllowedPeriod=safetyAllowedPeriod, overrideReason=overrideReason, orderAdditionalInstructions=orderAdditionalInstructions, orderReason=orderReason, courseStatus=courseStatus, courseDiscontinuedDate=courseDiscontinuedDate, courseDiscontinuedTime=courseDiscontinuedTime, courseWrittenDate=courseWrittenDate, courseWrittenTime=courseWrittenTime, authNumberofRepeatsAllowed=authNumberofRepeatsAllowed, authValidityPeriodDate=authValidityPeriodDate, authValidityPeriodTime=authValidityPeriodTime, dispenseInstruction=dispenseInstruction, dispenseAmountDescription=dispenseAmountDescription, dispenseAmount=dispenseAmount, dispenseAmountUnits=dispenseAmountUnits, dispenseDurationofSupply=dispenseDurationofSupply, orderComment=orderComment, orderID=orderID, userID=userID)
        db.session.add(prescription)
        db.session.commit()
        result = {
            "status": "Prescription added",
        }
        return jsonify(result), 200
    return jsonify({'status':'unsuccessful',
                    'message':"Invalid Token"}),401

# Doctor POST Past History Of Illness
@app.route('/api/doctor/past/<int:page_id>', methods=['POST'])
@cross_origin()
def edit_patient_page(page_id):
    frontToken = str(request.headers.get('x-access-token'))
    if request.method == 'POST' and doctorDict[currentDict['current']]==frontToken:
        past_history = past_history_of_illness.query.filter_by(user_id=page_id)
        immune = immunisation.query.filter_by(user_id=page_id)
        patient = db.session.query(Patients).filter()
        patient_information = past_history_of_illness(problem=request.json['problem'],
                                                      body_site=request.json['body_site'],
                                                      dateTime=request.json['dateTime'],
                                                      severity=request.json['severity'],
                                                      last_updated=request.json['last_updated'],
                                                      user_id=page_id)
        if patient_information.problem is None:
            result = {
                "status": "unsuccessful",
                "message": "Problem cannot be empty"
            }
            return jsonify(result), 411
        elif patient_information.body_site is None:
            result = {
                "status": "unsuccessful",
                "message": "Body_site cannot be empty"
            }
            return jsonify(result), 411
        elif patient_information.dateTime is None:
            result = {
                "status": "unsuccessful",
                "message": "Date-Time cannot be empty"
            }
            return jsonify(result), 411
        elif patient_information.severity is None:
            result = {
                "status": "unsuccessful",
                "message": "Severity cannot be empty"
            }
            return jsonify(result), 411
        elif patient_information.last_updated is None:
            result = {
                "status": "unsuccessful",
                "message": "Last-Updated cannot be empty"
            }
            return jsonify(result), 411
        jsondata = request.json
        if "id" in jsondata:
            patient_update = db.session.query(
                past_history_of_illness).filter_by(id=request.json['id']).first()
            patient_update.problem = patient_information.problem
            patient_update.body_site = patient_information.body_site
            patient_update.dateTime = patient_information.dateTime
            patient_update.severity = patient_information.severity
            patient_update.last_updated = patient_information.last_updated
            db.session.commit()
            result = {
                "status": "successful",
                "page_id": page_id
            }
            return jsonify(result), 200
            # print(product_update.name)
        else:
            db.session.add(patient_information)
            db.session.commit()
            # login_user(user_to_create)
            result = {
                "status": "successful",
                "page_id": page_id,
                "token": session.get('doctorToken')
            }
            print(session.get('doctorToken'))
            return jsonify(result), 200
    return jsonify({"status":"unsuccessful", "message":"Invalid Token"})
        
# User GET Past History Of Illness
@app.route("/api/past/<int:page_id>", methods=["GET"])
@cross_origin()
def get_past(page_id):
    frontToken = str(request.headers.get('x-access-token'))
    if request.method == "GET" and tokenDict[page_id]!=frontToken:
        return Response("Invalid Token", status=401, mimetype='application/json')
    past_history = past_history_of_illness.query.filter_by(user_id=page_id)
    s = json.dumps([r.as_dict() for r in past_history])
    return s, 200

# Doctor POST Immunisation
@app.route('/api/doctor/immunisation/<int:page_id>', methods=['POST'])
@cross_origin()
def edit_immunisation_page(page_id):
    frontToken = str(request.headers.get('x-access-token'))
    if request.method == 'POST' and doctorDict[currentDict['current']]==frontToken:
        immune = immunisation.query.filter_by(user_id=page_id)
        patient = db.session.query(Patients).filter()
        immunisationjson = immunisation(immunisation_item=request.json['immunisation_item'],
                                        route=request.json['route'],
                                        target_site=request.json['target_site'],
                                        sequence_no=request.json['sequence_no'],
                                        user_id=page_id)
        if immunisationjson.immunisation_item is None:
            result = {
                "status": "unsuccessful",
                "message": "Immunisation Item cannot be empty"
            }
            return jsonify(result), 411
        elif immunisationjson.route is None:
            result = {
                "status": "unsuccessful",
                "message": "Route cannot be empty"
            }
            return jsonify(result), 411
        elif immunisationjson.target_site is None:
            result = {
                "status": "unsuccessful",
                "message": "Target Site cannot be empty"
            }
            return jsonify(result), 411
        elif immunisationjson.sequence_no is None:
            result = {
                "status": "unsuccessful",
                "message": "Sequence Number cannot be empty"
            }
            return jsonify(result), 411
        jsondata = request.json
        if "id" in jsondata:
            immunisation_update = db.session.query(
                immunisation).filter_by(id=request.json['id']).first()
            immunisation_update.immunisation_item = immunisationjson.immunisation_item
            immunisation_update.route = immunisationjson.route
            immunisation_update.target_site = immunisationjson.target_site
            immunisation_update.sequence_no = immunisationjson.sequence_no
            immunisation_update.user_id = immunisationjson.user_id
            db.session.commit()
            # print(product_update.name)
            result = {
                "status": "successful",
                "page_id": page_id,
                "immunisation_item": immunisationjson.immunisation_item,
                "user_id": immunisationjson.user_id
            }
            return jsonify(result), 200

        else:
            db.session.add(immunisationjson)
            db.session.commit()
            result = {
                "status": "successful",
                "page_id": page_id,
                "immunisation_item": immunisationjson.immunisation_item,
                "user_id": immunisationjson.user_id
            }
            return jsonify(result), 200

# User GET Immunisation
@app.route("/api/immunisation/<int:page_id>", methods=["GET"])
@cross_origin()
def get_immunisation(page_id):
    frontToken = str(request.headers.get('x-access-token'))
    print("frontToken---------------------------    ",frontToken)
    if request.method == "GET" and tokenDict[page_id]!=frontToken:
        return Response("Invalid Token", status=401, mimetype='application/json')
    pimmune = immunisation.query.filter_by(user_id=page_id)
    s = json.dumps([r.as_dict() for r in pimmune])
    return s, 200

# Schedule Meet
@app.route("/api/schedule", methods=['GET', 'POST'])
@cross_origin()
def indexone():
    email = request.json["email"]
    eventlink = createEvent(email)
    msg = Message(
        'Hello',
        sender=('Sid From InCare', 'siddhukanu3@gmail.com'),
        recipients=[email]
    )
    msg.html = render_template('email.html', eventlink=eventlink)
    mail.send(msg)
    flash(f"Meeting link has been sent")
    result = {
        "status": "sent",
        "eventLink": eventlink
    }
    return jsonify(result), 200
