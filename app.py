from flask.json import JSONEncoder
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from flask import Flask, request, jsonify, redirect, Response
import json
import uuid
import time
from bson import ObjectId,json_util
class JSONEncoder(json.JSONEncoder):
        def default(self,o):
            if isinstance(o,ObjectId):
                return str(o)
            return json.JSONEncoder.default(self, o)

# Connect to our local MongoDB
client = MongoClient('mongodb://localhost:27017/')

# Choose database
db = client['InfoSys']

# Choose collections
students = db['Students']
users = db['Users']

# Initiate Flask App
app = Flask(__name__)

users_sessions = {}

def create_session(username):
    user_uuid = str(uuid.uuid1())
    users_sessions[user_uuid] = (username, time.time())
    return user_uuid  

def is_session_valid(user_uuid):
    return user_uuid in users_sessions

# ΕΡΩΤΗΜΑ 1: Δημιουργία χρήστη
@app.route('/createUser', methods=['POST'])
def create_user():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "username" in data or not "password" in data:
        return Response("Information incomplete",status=500,mimetype='application/json')
    
    
     
    if users.count_documents({'username':data['username']})>0:
         return Response("A user with the given email already exists", mimetype='application/json',status=400) 
    else:
        users.insert_one(data)
        return Response(data['username']+" was added to the MongoDB", mimetype='application/json',status=200) 
        
    # ΕΡΩΤΗΜΑ 2: Login στο σύστημα
@app.route('/login', methods=['POST'])
def login():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "username" in data or not "password" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")

    """
        Να καλεστεί η συνάρτηση create_session() (!!! Η ΣΥΝΑΡΤΗΣΗ create_session() ΕΙΝΑΙ ΗΔΗ ΥΛΟΠΟΙΗΜΕΝΗ) 
        με παράμετρο το username μόνο στη περίπτωση που τα στοιχεία που έχουν δοθεί είναι σωστά, δηλαδή:
        * το data['username] είναι ίσο με το username που είναι στη ΒΔ (να γίνει αναζήτηση στο collection Users) ΚΑΙ
        * το data['password'] είναι ίσο με το password του συγκεκριμένου χρήστη.
        * Η συνάρτηση create_session() θα επιστρέφει ένα string το οποίο θα πρέπει να αναθέσετε σε μία μεταβλητή που θα ονομάζεται user_uuid.
        
        * Αν γίνει αυθεντικοποίηση του χρήστη, να επιστρέφεται μήνυμα με status code 200. 
        * Διαφορετικά, να επιστρέφεται μήνυμα λάθους με status code 400.
    """

    if users.count_documents( { '$and': [{'username':data['username']}, {'password':data['password']}]})>0:
        user_uuid=create_session(data['username'])
        res = {"uuid": user_uuid, "username": data['username']}
        return Response(json.dumps(res), mimetype='application/json',status=200) # ΠΡΟΣΘΗΚΗ STATUS

    else:
        return Response("Wrong username or password.",mimetype='application/json',status=400) # ΠΡΟΣΘΗΚΗ STATUS


# ΕΡΩΤΗΜΑ 3: Επιστροφή φοιτητή βάσει email 
@app.route('/getStudent', methods=['GET'])
def get_student():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
    uuid = request.headers.get('Authorization')
    if  is_session_valid(uuid):
        if students.count_documents({'email':data['email']})>0:
            student=students.find_one({'email':data['email']})
      
            return Response(JSONEncoder().encode(student), status=200, mimetype='application/json')
        else:
            return Response("student was not found " ,status=400, mimetype='application/json')
    else:
                   return Response("user not authenticated" ,status=401, mimetype='application/json')

    """
        Στα headers του request ο χρήστης θα πρέπει να περνάει το uuid το οποίο έχει λάβει κατά την είσοδό του στο σύστημα. 
            Π.Χ: uuid = request.headers.get['authorization']
        Για τον έλεγχο του uuid να καλεστεί η συνάρτηση is_session_valid() (!!! Η ΣΥΝΑΡΤΗΣΗ is_session_valid() ΕΙΝΑΙ ΗΔΗ ΥΛΟΠΟΙΗΜΕΝΗ) με παράμετρο το uuid. 
            * Αν η συνάρτηση επιστρέψει False ο χρήστης δεν έχει αυθεντικοποιηθεί. Σε αυτή τη περίπτωση να επιστρέφεται ανάλογο μήνυμα με response code 401. 
            * Αν η συνάρτηση επιστρέψει True, ο χρήστης έχει αυθεντικοποιηθεί. 

        Το συγκεκριμένο endpoint θα δέχεται σαν argument το email του φοιτητή και θα επιστρέφει τα δεδομένα του. 
        Να περάσετε τα δεδομένα του φοιτητή σε ένα dictionary που θα ονομάζεται student.
        
        Σε περίπτωση που δε βρεθεί κάποιος φοιτητής, να επιστρέφεται ανάλογο μήνυμα.
    """

    # Η παρακάτω εντολή χρησιμοποιείται μόνο στη περίπτωση επιτυχούς αναζήτησης φοιτητών (δηλ. υπάρχει φοιτητής με αυτό το email).
    
# ΕΡΩΤΗΜΑ 4: Επιστροφή όλων των φοιτητών που είναι 30 ετών
@app.route('/getStudents/thirties', methods=['GET'])
def get_students_thirtys():
    """
        Στα headers του request ο χρήστης θα πρέπει να περνάει το uuid το οποίο έχει λάβει κατά την είσοδό του στο σύστημα. 
            Π.Χ: uuid = request.headers.get['authorization']
        Για τον έλεγχο του uuid να καλεστεί η συνάρτηση is_session_valid() (!!! Η ΣΥΝΑΡΤΗΣΗ is_session_valid() ΕΙΝΑΙ ΗΔΗ ΥΛΟΠΟΙΗΜΕΝΗ) με παράμετρο το uuid. 
            * Αν η συνάρτηση επιστρέψει False ο χρήστης δεν έχει αυθεντικοποιηθεί. Σε αυτή τη περίπτωση να επιστρέφεται ανάλογο μήνυμα με response code 401. 
            * Αν η συνάρτηση επιστρέψει True, ο χρήστης έχει αυθεντικοποιηθεί. 
        
        Το συγκεκριμένο endpoint θα πρέπει να επιστρέφει τη λίστα των φοιτητών οι οποίοι είναι 30 ετών.
        Να περάσετε τα δεδομένα των φοιτητών σε μία λίστα που θα ονομάζεται students.
        
        Σε περίπτωση που δε βρεθεί κάποιος φοιτητής, να επιστρέφεται ανάλογο μήνυμα και όχι κενή λίστα.
    """
    
    # Η παρακάτω εντολή χρησιμοποιείται μόνο σε περίπτωση επιτυχούς αναζήτησης φοιτητών (δηλ. υπάρχουν φοιτητές που είναι 30 ετών).
    uuid = request.headers.get('Authorization')
    if  is_session_valid(uuid):
        if students.count_documents({'yearOfBirth':1991})!=0:
            jasons=[]
            for i in students.find({'yearOfBirth':1991}):
                jason=json.dumps(i,default=json_util.default)
                jasons.append(jason)
            return Response(jasons, status=200, mimetype='application/json')
        else:
            return Response("there are no 30 years old students" ,status=400, mimetype='application/json')
    else:
                   return Response("user not authenticated" ,status=401, mimetype='application/json')

    """
         return Response(JSONEncoder().encode(students), status=200, mimetype='application/json')
    else:
        return Response("there are no 30 years old students" ,status=400, mimetype='application/json')
   """

    # ΕΡΩΤΗΜΑ 5: Επιστροφή όλων των φοιτητών που είναι τουλάχιστον 30 ετών
@app.route('/getStudents/oldies', methods=['GET'])
def get_students_thirty():
    uuid = request.headers.get('Authorization')
    if  is_session_valid(uuid):
        if students.count_documents({'yearOfBirth':{ '$lte':1991}})!=0:
            jasons=[]
            for i in students.find({'yearOfBirth':{'$lte':1991}}):
                jason=json.dumps(i,default=json_util.default)
                jasons.append(jason)
            return Response(jasons, status=200, mimetype='application/json')
        else:
            return Response("there are no students 30 years old or older" ,status=400, mimetype='application/json')
   

# ΕΡΩΤΗΜΑ 6: Επιστροφή φοιτητή που έχει δηλώσει κατοικία βάσει email 
@app.route('/getStudentAddress', methods=['GET'])
def get_students():

    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
    uuid = request.headers.get('Authorization')
    if  is_session_valid(uuid):
        if students.count_documents({'$and': [{'email':data['email']},{'address.street':{'$exists':1}}]})>0:
            student=students.find_one({'$and': [{'email':data['email']},{'address.street':{'$exists':1}}]},{'address.postcode':1,'address.street':1,'name':1,'_id':0})
        
            
            return Response(JSONEncoder().encode(student), status=200, mimetype='application/json')
        else:
            return Response("student was not found " ,status=400, mimetype='application/json')
    else:
                   return Response("user not authenticated" ,status=401, mimetype='application/json')

   

# ΕΡΩΤΗΜΑ 7: Διαγραφή φοιτητή βάσει email 
@app.route('/deleteStudent', methods=['DELETE'])
def delete_student():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
    uuid = request.headers.get('Authorization')
    if  is_session_valid(uuid):
        if students.count_documents({'email':data['email']})>0:
            name=students.find_one({'email':data['email']},{'name':1,'_id':0})
            name=json.dumps(name)
            msg=name+"was deleted"
            students.delete_one({'email':data['email']})
            return Response(msg, status=200, mimetype='application/json')
        else:
            return Response('no student was found', status=400, mimetype='application/json')
    else:
                   return Response("user not authenticated" ,status=401, mimetype='application/json')


## ΕΡΩΤΗΜΑ 8: Εισαγωγή μαθημάτων σε φοιτητή βάσει email 
@app.route('/addCourses', methods=['PATCH'])
def add_courses():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data or not "courses" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
    uuid = request.headers.get('Authorization')
    if  is_session_valid(uuid):
        if students.count_documents({'email':data['email']})>0:
            students.update({'email':data['email']},{'$set':{'courses':data['courses']}})
            student=students.find_one({'email':data['email']})
            return Response(JSONEncoder().encode(student), status=200, mimetype='application/json')
        else: 
            return Response('student was not found', status=400, mimetype='application/json')
    else:
                   return Response("user not authenticated" ,status=401, mimetype='application/json')


# ΕΡΩΤΗΜΑ 9: Επιστροφή περασμένων μαθημάτων φοιτητή βάσει email
@app.route('/getPassedCourses', methods=['GET'])
def get_courses():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
    uuid = request.headers.get('Authorization')
    if  is_session_valid(uuid):    
        if students.count_documents({'$and': [{'email':data['email']},{'courses':{'$exists':1}}]})!=0:
            ctr=0;
            st=students.find_one({'email':data['email']})
            student={}
       
            for i in st['courses']:
                vals=list(i.values())
                keyz=list(i.keys())
                for k in vals:
                    if k>5 :
                         student[keyz[0]]=k
                         ctr=ctr+1
                      
            print(student)
            if ctr>0:
                return Response(JSONEncoder().encode(student), status=200, mimetype='application/json')
            else:
                                return Response('email not found or student has no passed classes', status=400, mimetype='application/json')

        else:
                return Response('email not found or student has no passed classes', status=400, mimetype='application/json')
    else:
                               return Response("user not authenticated" ,status=401, mimetype='application/json')

    
# Εκτέλεση flask service σε debug mode, στην port 5000. 
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)