from flask import render_template,url_for,redirect,flash,request, abort
from flaskblog.form import PostForm, RegistrationForm,LoginForm,UpdateAccountForm,PostForm,RequestResetForm,PasswordResetForm
from flaskblog.models import User,Post
from flaskblog import app,db,bcrypt,mail
from flask_login import login_user,current_user,logout_user,login_required
import secrets,os
from PIL import Image
from flask_mail import Message

@app.route('/home')
@app.route('/')
def home():
    page=request.args.get('page',1,type=int)
    posts=Post.query.order_by(Post.date_posted.desc()).paginate(page=page,per_page=5)
    return render_template('home.html',title='Home',posts=posts)

@app.route('/about')
def about():
    return render_template('about.html',title='About')

@app.route('/login',methods=['POST','GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user,form.remember.data)
            next_page=request.args.get('next')
            flash('Logged in!','success')
            if(next_page):
                return redirect(next_page)
            else:
                return redirect(url_for('home'))
        else:
            flash(f'Login unsuccessful. Please check your email and password','danger')
    return render_template('login.html',title='Login',form=form)

@app.route('/register',methods=['POST','GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=RegistrationForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user=User(username=form.username.data,email=form.email.data,password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created. You can now log in!','success')
        return redirect(url_for('login'))
    return render_template('register.html',title='Register',form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login')) 

def saveProfilePicture(picture_data):
    random=secrets.token_hex(8)
    _,ext=os.path.splitext(picture_data.filename)
    profile_pic=random+ext
    picture_path=os.path.join(app.root_path,'static',profile_pic)
    size=(200,200)
    resized_image=Image.open(picture_data)
    resized_image.thumbnail(size)
    resized_image.save(picture_path)
    return profile_pic

@app.route('/account',methods=['POST','GET'])
@login_required
def account():
    form=UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            profile_pic=saveProfilePicture(form.picture.data)
            current_user.image_file=profile_pic
        current_user.username=form.username.data
        current_user.email=form.email.data
        db.session.commit()
        flash('Your account has been updated!','success')
        return redirect(url_for('account'))
    elif request.method=='GET':
        form.username.data=current_user.username
        form.email.data=current_user.email
    image_file=url_for('static',filename=current_user.image_file)
    return render_template('account.html',title='Account',image_file=image_file,form=form)

@app.route('/post/new_post', methods=['POST','GET'])
@login_required
def new_post():
    form=PostForm()
    if form.validate_on_submit():
        flash("Your post has been created!",'success')
        post=Post(title=form.title.data,content=form.content.data,author=current_user)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('new_post.html',title="New Post",form=form,legend="Create new post")

@app.route('/post/<int:post_id>', methods=['POST','GET'])
def post(post_id):
    post=Post.query.get_or_404(post_id)
    return render_template('post.html',title=post.title,post=post)

@app.route('/post/<int:post_id>/update', methods=['POST','GET'])
@login_required
def update_post(post_id):
    post=Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form=PostForm()
    if form.validate_on_submit():
        post.title=form.title.data
        post.content=form.content.data
        db.session.commit()
        flash('Your post has been updated!','success')
        return redirect(url_for('post',post_id=post.id))
    elif request.method=='GET':        
        form.title.data=post.title
        form.content.data=post.content
    return render_template('new_post.html',title="Update Post",form=form,legend="Update post")

@app.route('/post/<int:post_id>/delete', methods=['GET','POST'])
@login_required
def delete_post(post_id):
    post=Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!','success')
    return redirect(url_for('home'))

@app.route('/user/<string:username>')
def user_posts(username):
    page=request.args.get('page',1,type=int)
    user=User.query.filter_by(username=username).first_or_404()
    posts=Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page,per_page=5)
    return render_template('user_posts.html',posts=posts,user=user,title=username)

def send_reset_email(user):
    token=user.get_reset_token()
    msg=Message('Password reset request',sender='ashishkaparwanask@gmail.com',recipients=[user.email])
    msg.body=f'''Visit the following link to reset your password:
{url_for('reset_token',token=token,_external=True)}
If you did not make any such request, you can safely ignore this mail.
'''
    mail.send(msg)

@app.route('/reset_password',methods=['POST','GET'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=RequestResetForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('Instructions regarding resetting your password have been sent to your email. In case you could not find one, please check your spam folder.','info')
        return redirect(url_for('login'))
    return render_template('reset_request.html',title='Reset password',form=form)

@app.route('/reset_password/<token>',methods=['POST','GET'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user=User.verify_reset_token(token)
    if user is None:
        flash('The token is invalid or it has expired','warning')
        return redirect(url_for('reset_password'))
    form=PasswordResetForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password=hashed_password
        db.session.commit()
        flash('Your password has been changed. You can now log in!','success')
        return redirect(url_for('login'))
    return render_template('reset_token.html',title='Reset password',form=form)