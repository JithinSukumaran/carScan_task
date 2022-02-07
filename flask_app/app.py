from flask import Flask,render_template,request,redirect,url_for
from flask_uploads import UploadSet,configure_uploads,ALL,DATA,IMAGES
from tensorflow.keras.models import load_model
from matplotlib.image import imread
import tensorflow_hub as hub
import cv2
import numpy as np
from PIL import Image
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storage.db'
db = SQLAlchemy(app)

class CarScan(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    image = db.Column(db.BLOB())
    status = db.Column(db.String(200))
    date_created = db.Column(db.DateTime,default=datetime.utcnow)

    def __repr__(self):
        return '<Car %r>'% self.id

model = load_model('static/model/mobilenewcar.h5',custom_objects={'KerasLayer': hub.KerasLayer})

photos = UploadSet('photos',IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'static/img'
configure_uploads(app,photos)

def readImage(img_name):
   try:
       fin = open(img_name, 'rb')
       img = fin.read()
       return img
   except:
       print("ERROR!!")

def is_damaged(image):
    image = imread('static/img/'+image)
    scaled_image = cv2.resize(image,(224,224))
    scaled_image = scaled_image/255
    scaled_image = scaled_image.reshape(1,224,224,3)
    return model.predict(scaled_image)

@app.route('/checkdata')
def check():
    cars = CarScan.query.order_by(CarScan.date_created).all()
    return render_template('data.html',cars=cars)

@app.route('/',methods=['POST','GET'])
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        filename = photos.save(request.files['photo'])
        answer = is_damaged(filename)
        answer = round(answer[0][0]*100,2)

        img_name = imread(f'static/img/{filename}')
        car_img_binary = np.where(img_name>128,255,0)

        add_status = CarScan(status = answer)
        print(type(add_status))
        add_image = CarScan(image = car_img_binary)
        try:
            db.session.add(add_status)
            db.session.add(add_image)
            db.session.commit()
        except:
            return 'There was a problem storing the image and status report'

        return render_template('index.html',filename=filename,answer = answer)
    return render_template('index.html',filename= 'default.jpeg',answer=0)


if __name__=='__main__':
    app.run(debug=True)
