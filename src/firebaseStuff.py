import pyrebase

firebaseConfig={"apiKey": "key",
    "authDomain": "domain",
    "projectId": "id",
    "storageBucket": "storage",
    "messagingSenderId": "",
    "appId": "",
    "measurementId": "",
    "databaseURL": ""}

firebase = pyrebase.initialize_app(firebaseConfig)

auth=firebase.auth()
db = firebase.database()



