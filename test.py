import firebase_admin
from firebase_admin import messaging, firestore
from firebase_admin._messaging_utils import Notification

cred = firebase_admin.credentials.Certificate('adminsdk.json')
app = firebase_admin.initialize_app(credential=cred)


message = messaging.Message(
    data={
        'title': 'Hello',
        'body': 'This is test message'
    },
    notification=Notification(title='Hello', body='How are you do?'),
    token='eYZOgpyPT16807aQ6JJAEV:APA91bEwKt4ViFvP3H4s0fUZd-1JFTrzs9i9HGXF1q_L2Cq2ZfZcg6BUQVcrqQqG6WnN6Qc1HOLejZfmhWH5Pwo4sShAQDjRq0k4vx4z_UitAM2zEhCd2j0rW-Gu3mdoMyH4Pn--VAjs'
)


result = messaging.send(message=message, app=app)

print(result)


