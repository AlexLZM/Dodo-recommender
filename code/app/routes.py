
import os
import json
from flask import render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import current_user, login_user, login_required, logout_user
from werkzeug.utils import secure_filename
from app import application, classes, db, features, transforms_valid, feature_model, id_list
import random
import boto3
import cv2
import torch
import numpy as np


def read_img(img_path, transform=None):
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # transform images
    res = transform(image=img)
    img = res['image']
    img = img.astype(np.float32)
    print(f'original shape {img.shape}')
    img = img.transpose(2,0,1) 

    return torch.tensor([img]).float()

@application.route('/')
@application.route('/index.html')
def index():
    """ searching main page"""
    return render_template('index.html')


@application.route('/about.html')
def about():
    """ a page about our team"""
    return render_template('about.html')


@application.route('/contact.html',methods=['GET', 'POST'])
def contact():
    """ a contact page"""
    if request.method == 'POST':
        
        name = request.form['name']
        email = request.form['email']
        comment = request.form['comment']

        with open('contact.csv', 'a') as con:
            con.write(f"\n{name},{email},{comment},")

        return redirect(url_for('contact'))

    return render_template('contact.html', api='') # api is left empty for privacy reason

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and \
           filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS


@application.route('/uploader', methods = ['POST'])
def upload_file():
    global id_list, similarities
    """a post page to receive file on client's machine"""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['file']
    print('got file')

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    print(f'file name is {file.filename}')
    if file and allowed_file(file.filename):
        print('extension ok')
        filename = secure_filename(file.filename)
        # save img to disk
        path = os.path.join(application.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        print(f'file saved to {path}')
        # upload img to s3
        ACCESS_ID='' # ACCESS_ID is left empty for privacy reason
        ACCESS_KEY='' # ACCESS_KEY is left empty for privacy reason
        s3_client = boto3.client('s3',
         aws_access_key_id=ACCESS_ID,
         aws_secret_access_key= ACCESS_KEY)
        while True:
            try:
                s3_client.Object(classes.upload_img_bucket, filename).load()
            except:
                break
            print('object detacted')
            filename = '1' + filename
            print(f'renamed to {filename}')

        s3_client.upload_file(path, classes.upload_img_bucket, filename)
        print(f'uploaded filename {filename} to S3')
        test_img = read_img(path, transform=transforms_valid)
        print(f'input image shape {test_img.shape}')
        feature_model.eval()
        test_img_fea = feature_model(test_img).detach().numpy()
        cosine_sims = test_img_fea@(features.T)
        print('cosine_sims shape')
        print(cosine_sims.shape)
        # update uploads table in s3
        img_path = classes.upload_img_bucket + "/" + filename
        # upload = classes.Uploads(image_path=img_path, embedding=list(test_img_fea.reshape(-1,).astype(np.float64)))
        # db.session.add(upload)
        # db.session.commit()

        order = (-1*cosine_sims).argsort(1)[:,:8].reshape(-1,)
        root = (os.path.abspath(os.path.dirname(__file__)))
        arr = np.load(root+'/arr.npy')
        ids = arr[order,0]
        similarities = tuple(cosine_sims[0,order])
        print('similarities:')
        for s in similarities:
            print(f'-- {s:.4f} --')
        id_list = tuple(ids.reshape(-1,)) 
        return redirect(url_for('result'))
    print('extension not allowd')
    flash(f"file type must be '.png', '.jpg', or '.jpeg")
    return redirect(url_for('index'))


@application.route('/shop.html')
def shop():
    """ a page shows search result"""

    basedir = os.path.abspath(os.path.dirname(__file__))
    f = open(basedir+"/static/database/qoo_output.json", "r")
    data = json.load(f)
    f.close()

    r_data = random.sample(data.items(), 8)

    it1 = f'static/database/qoo_img/{r_data[0][0]}.jpg'
    it1_dict = r_data[0][1]
    it2 = f'static/database/qoo_img/{r_data[1][0]}.jpg'
    it2_dict = r_data[1][1]
    it3 = f'static/database/qoo_img/{r_data[2][0]}.jpg'
    it3_dict = r_data[2][1]
    it4 = f'static/database/qoo_img/{r_data[3][0]}.jpg'
    it4_dict = r_data[3][1]
    it5 = f'static/database/qoo_img/{r_data[4][0]}.jpg'
    it5_dict = r_data[4][1]
    it6 = f'static/database/qoo_img/{r_data[5][0]}.jpg'
    it6_dict = r_data[5][1]
    it7 = f'static/database/qoo_img/{r_data[6][0]}.jpg'
    it7_dict = r_data[6][1]
    it8 = f'static/database/qoo_img/{r_data[7][0]}.jpg'
    it8_dict = r_data[7][1]

    return render_template('shop.html', **locals())
    

        
@application.route('/result.html')
def result():
    global id_list
    """ a page shows search result"""
    
    print(f'got id_list {id_list}')
    if not id_list:
        basedir = os.path.abspath(os.path.dirname(__file__))
        f = open(basedir+"/static/database/qoo_output.json", "r")
        data = json.load(f)
        f.close()

        r_data = random.sample(data.items(), 8)

        it1 = f'static/database/qoo_img/{r_data[0][0]}.jpg'
        it1_dict = r_data[0][1]
        it2 = f'static/database/qoo_img/{r_data[1][0]}.jpg'
        it2_dict = r_data[1][1]
        it3 = f'static/database/qoo_img/{r_data[2][0]}.jpg'
        it3_dict = r_data[2][1]
        it4 = f'static/database/qoo_img/{r_data[3][0]}.jpg'
        it4_dict = r_data[3][1]
        it5 = f'static/database/qoo_img/{r_data[4][0]}.jpg'
        it5_dict = r_data[4][1]
        it6 = f'static/database/qoo_img/{r_data[5][0]}.jpg'
        it6_dict = r_data[5][1]
        it7 = f'static/database/qoo_img/{r_data[6][0]}.jpg'
        it7_dict = r_data[6][1]
        it8 = f'static/database/qoo_img/{r_data[7][0]}.jpg'
        it8_dict = r_data[7][1]

        return render_template('shop.html', **locals())
    else:
        df = classes.Candidates.query.filter(classes.Candidates.id.in_(id_list)).all()
        params = {}
        for i, id in enumerate(id_list, 1):
            # print(f'i = {i}')
            row = classes.Candidates.query.filter_by(id=id).first()
            params['it'+str(i)] = f"https://deep-fashion-pic-resources.s3.amazonaws.com/{row.image_path.split('/')[-1]}"
            params['it'+str(i)+'_dict'] = {}
            params['it'+str(i)+'_dict']['url'] = row.url
            params['it'+str(i)+'_dict']['item'] = row.name
            params['it'+str(i)+'_dict']['price'] = f'{row.original_price:.0f}'+' '+str(row.currency)
            params['it'+str(i)+'_dict']['stock'] = ' ' if row.stock is None else row.stock

        return render_template('shop.html', **params)

@application.route('/login.html',methods=['GET', 'POST'])
def login():
    """ a page to login"""
    if request.method == 'POST':

        lemail = request.form['lemail']
        lpwd = request.form['lpwd']
        user = classes.Users.query.filter_by(email=lemail).first()
        # Login and validate the user.
        if user is not None and user.check_password(lpwd):
            login_user(user)
            return redirect(url_for('account'))
        else:
            return '<h1>Error - password is incorrect</h1>'

    if current_user.is_authenticated:
        return render_template('account.html')

    return render_template('login.html')


@application.route('/account.html')
@login_required
def account():
    name = current_user.fname + ' ' + current_user.lname
    return render_template('account.html', name=name)


@application.route('/logout')
@login_required
def logout():

    logout_user()

    return render_template('index.html')


@application.route('/regis.html',methods=['GET', 'POST'])
def regis():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        mobile = request.form['mobile']
        email = request.form['email']
        pwd = request.form['pwd']
        rpwd = request.form['rpwd']

        user_count = classes.Users.query.filter_by(email=email).count()
        if user_count > 0:
            return '<h1>Error - Existing user : ' + email + '</h1>'
        elif pwd != rpwd:
            return '<h1>Error - password is not the same</h1>'
        else:
            user = classes.Users(fname, lname, mobile, email, pwd)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('account'))

    return render_template('regis.html')