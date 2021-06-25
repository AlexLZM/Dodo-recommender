import os
import json
from flask import render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import current_user, login_user, login_required, logout_user
from werkzeug.utils import secure_filename
from app import application, classes, db, features, transforms_valid, feature_model, id_list, arr
from flask_paginate import Pagination, get_page_parameter
import random
import boto3
import cv2
import torch
import numpy as np
import pandas as pd
from tqdm import tqdm
import time
from flask import session
import requests
import mimetypes
from io import BytesIO
import magic

# keys deleted for privacy reason
ACCESS_ID='' 
ACCESS_KEY=''
API = '' 

VALID_IMAGE_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
]


VALID_IMAGE_MIMETYPES = [
    "image"
]



def get_mimetype(fobject):
    mime = magic.Magic(mime=True)
    mimetype = mime.from_buffer(fobject.read(1024))
    fobject.seek(0)
    return mimetype

def valid_image_mimetype(fobject):
    mimetype = get_mimetype(fobject)
    if mimetype:
        return mimetype.startswith('image')
    else:
        return False





def read_img(img_path, transform=None):
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    res = transform(image=img)
    img = res['image']
    img = img.astype(np.float32)
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

    return render_template('contact.html', api=API)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and \
           filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS


@application.route('/shop.html')
def shop():
    """ a page shows search result"""
    
    select = request.args.get('filter')
    lower = request.args.get('lower')
    upper = request.args.get('upper')
    up = upper if upper else 1<<30
    low = lower if lower else -(1<<30)
    if select in {'bags', 'clothes'}:
        id_list_all = db.session.query(classes.Candidates.id).\
        filter(classes.Candidates.price_usd>low, 
            classes.Candidates.price_usd<up, 
            classes.Candidates.org_cat == select).all()[::-1]
    elif select == 'stock':
        id_list_all = db.session.query(classes.Candidates.id).\
        filter(classes.Candidates.price_usd>low, 
            classes.Candidates.price_usd<up, 
            classes.Candidates.stock == 'in stock').all()[::-1]
    else:
        id_list_all = db.session.query(classes.Candidates.id).\
        filter(classes.Candidates.price_usd>low, 
            classes.Candidates.price_usd<up).all()[::-1]
    id_list_all = random.sample(id_list_all,160)
    def get_ids(offset=0, per_page=8):
        return id_list_all[offset: offset + per_page]
    page = request.args.get(get_page_parameter(), type=int, default=1)
    total = len(id_list_all)
    pagination_ids = get_ids(offset=(page-1)*8, per_page=8)

    pagination = Pagination(page=page, per_page=8, total=total,
                            css_framework='semantic')
    pagination_items = []
    for id in (pagination_ids):
        row = classes.Candidates.query.filter_by(id=id[0]).first()
        pagination_items.append({})
        pagination_items[-1]['url'] = row.url
        pagination_items[-1]['item'] = row.name
        pagination_items[-1]['img'] = f"https://deep-fashion-pic-resources.s3.amazonaws.com/{row.image_path.split('/')[-1]}"
        pagination_items[-1]['similarity'] = "Sale!"
        pagination_items[-1]['price'] = f'{row.original_price:.0f}'+' '+str(row.currency)
        pagination_items[-1]['usd_price'] = f'{row.price_usd:.0f}'+' USD'
        pagination_items[-1]['currency'] = f'{row.currency}'
        pagination_items[-1]['stock'] = ' ' if row.stock is None else row.stock

    
    return render_template('shop.html', **locals())


@application.route('/uploader', methods = ['GET','POST'])
def upload_file():
    """a post page to receive file on client's machine"""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['file']
    
    if file.filename == '':
        url = request.form['url']
        if url is not None and url is not '':
            
            img_bytes = requests.get(url).content
            fobject = BytesIO(img_bytes)
            if not valid_image_mimetype(fobject):
                flash('Not a valid image url')
                return redirect(url_for('index'))

            filename = str(time.time()) + '.img'
            # save img to disk
            path = os.path.join(application.config['UPLOAD_FOLDER'], filename)
            with open(path, 'wb') as f:
                f.write(img_bytes)

            # upload img to s3
            
            s3_client = boto3.client('s3',
             aws_access_key_id=ACCESS_ID,
             aws_secret_access_key= ACCESS_KEY)

            s3_client.upload_file(path, classes.upload_img_bucket, filename)
            
            test_img = read_img(path, transform=transforms_valid)
            feature_model.eval()
            test_img_fea = feature_model(test_img).detach().numpy()
            session['user_img'] = path
            session['test_img_fea'] = test_img_fea.tolist()
            img_path = classes.upload_img_bucket + "/" + path.split('/')[-1]
            upload = classes.Uploads(image_path=img_path, embedding=list(test_img_fea.reshape(-1,).astype(np.float64)))
            db.session.add(upload)
            db.session.commit()
            return redirect(url_for('result'))
            

            
        else:
            flash('No selected file and url is empty')
            return redirect(url_for('index'))





        flash('No selected file')
        return redirect(url_for('index'))
    if file and allowed_file(file.filename):
        filename = str(time.time()) + secure_filename(file.filename)
        # save img to disk
        path = os.path.join(application.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        # upload img to s3
        
        s3_client = boto3.client('s3',
         aws_access_key_id=ACCESS_ID,
         aws_secret_access_key= ACCESS_KEY)

        s3_client.upload_file(path, classes.upload_img_bucket, filename)
        
        test_img = read_img(path, transform=transforms_valid)
        feature_model.eval()
        test_img_fea = feature_model(test_img).detach().numpy()
        session['user_img'] = path
        session['test_img_fea'] = test_img_fea.tolist()
        img_path = classes.upload_img_bucket + "/" + path.split('/')[-1]
        upload = classes.Uploads(image_path=img_path, embedding=list(test_img_fea.reshape(-1,).astype(np.float64)))
        db.session.add(upload)
        db.session.commit()
        return redirect(url_for('result'))

    flash(f"file type must be '.png', '.jpg', or '.jpeg")
    return redirect(url_for('index'))




        
@application.route('/result.html')
def result():
    path = session['user_img']
    test_img_fea = session['test_img_fea']
    cosine_sims = np.array(test_img_fea)@(features.T)
 
    order = (-1*cosine_sims).argsort(1).reshape(-1,)
    data = pd.DataFrame(arr[order,:], columns=['id','cat','price','img','stock'])
    data['sims'] = cosine_sims[0,order].reshape(-1,)
    select = request.args.get('filter')
    lower = request.args.get('lower')
    upper = request.args.get('upper')
    up = float(upper) if upper else 1<<30
    low = float(lower) if lower else -(1<<30)
    if select in {'bags', 'clothing'}:
        id_list_all = data[(data['cat']==select) & (data.price>low) & (data.price<up)]

    elif select == 'stock':
        id_list_all = data[(data['stock']=='in stock') & (data.price>low) & (data.price<up)]
    else:
        id_list_all = data[(data.price>low) & (data.price<up)]
    
    id_list_all = id_list_all.iloc[:160]
    def get_ids(offset=0, per_page=8):
        return id_list_all.iloc[offset: offset + per_page]
    page = request.args.get(get_page_parameter(), type=int, default=1)
    total = len(id_list_all)
    pagination_ids = get_ids(offset=(page-1)*8, per_page=8)
    pagination = Pagination(page=page, per_page=8, total=total,
                            css_framework='semantic')
    pagination_items = []
    for i in (pagination_ids.index):
        row = classes.Candidates.query.filter_by(id=pagination_ids.loc[i,'id']).first()
        pagination_items.append({})
        pagination_items[-1]['url'] = row.url
        pagination_items[-1]['item'] = row.name
        pagination_items[-1]['img'] = f"https://deep-fashion-pic-resources.s3.amazonaws.com/{row.image_path.split('/')[-1]}"
        pagination_items[-1]['similarity'] = f"{id_list_all.loc[i, 'sims']*100:.1f}%"
        pagination_items[-1]['price'] = f'{row.original_price:.0f}'+' '+str(row.currency)
        pagination_items[-1]['usd_price'] = f'{row.price_usd:.0f}'+' USD'
        pagination_items[-1]['currency'] = f'{row.currency}'
        pagination_items[-1]['stock'] = ' ' if row.stock is None else row.stock
    user_pic=f"/static/uploads/{path.split('/')[-1]}"
    return render_template('result.html', **locals())

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
            flash('Error - username or password is invalid')

    if current_user.is_authenticated:
        return render_template('account.html')

    return render_template('login.html')


@application.route('/account.html')
@login_required
def account():
    name = current_user.fname + ' ' + current_user.lname
    username = current_user.email
    mobile = current_user.mobile
    return render_template('account.html', name=name, username=username, mobile=mobile)


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
            flash('Error - Existing user')
        elif pwd != rpwd:
            flash('Error - password is not the same')
        else:
            user = classes.Users(fname, lname, mobile, email, pwd)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('account'))

    return render_template('regis.html')


@application.route('/reset_password.html',methods=['GET', 'POST'])
@login_required
def reset_password():
    if request.method == 'POST':
        opwd = request.form['opwd']
        npwd = request.form['npwd']
        npwd2 = request.form['npwd2']
        userid = current_user.id
        user = classes.User.query.filter_by(id=userid).first()
        if not user.check_password(opwd):
            flash('Error - Invalid old password')
        elif npwd != npwd2:
            flash('Error - password is not the same')
        else:
            user.set_password(npwd)
            db.session.commit()
            return redirect(url_for('account'))

    return render_template('reset_password.html')


@application.route('/reset_email.html',methods=['GET', 'POST'])
@login_required
def reset_email():
    if request.method == 'POST':
        nemail = request.form['nemail']
        nemail2 = request.form['nemail2']
        pwd = request.form['pwd']
        userid = current_user.id
        user = classes.User.query.filter_by(id=userid).first()
        if not user.check_password(pwd):
            flash('Error - Invalid old password')
        elif nemail != nemail2:
            flash('Error - email is not the same')
        else:
            user.email = nemail
            db.session.commit()
            return redirect(url_for('account'))

    return render_template('reset_email.html')


@application.route('/reset_name.html',methods=['GET', 'POST'])
@login_required
def reset_name():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        mobile = request.form['mobile']
        userid = current_user.id
        user = classes.User.query.filter_by(id=userid).first()
        user.fname = fname
        user.lname = lname
        user.mobile = mobile
        db.session.commit()
        return redirect(url_for('account'))

    return render_template('reset_name.html')
