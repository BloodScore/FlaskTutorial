from datetime import datetime
from langdetect import detect
from flask import request, g, jsonify
from flask_babel import get_locale
from flask import render_template, flash, redirect, url_for, current_app
from flask_login import current_user, login_required
from app import db
from app.main import main_bp
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm
from app.models import User, Post
from app.translate import translate


@main_bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@main_bp.route('/', methods=['GET', 'POST'])
@main_bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        language = detect(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None
    return render_template(
        'main/index.html',
        title='Home',
        form=form,
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url
    )


@main_bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('main/index.html', title='Explore', posts=posts.items, next_url=next_url, prev_url=prev_url)


@main_bp.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.profile', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.profile', username=user.username, page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template(
        'main/profile.html',
        user=user,
        posts=posts.items,
        form=form,
        next_url=next_url,
        prev_url=prev_url
    )


@main_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.profile', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('main/edit_profile.html', title='Edit Profile', form=form)


@main_bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        flash(f'User {username} not found.')
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('main.profile', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(f'You are now following {username}!')
    return redirect(url_for('main.profile', username=username))


@main_bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        flash(f'User {username} not found.')
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('main.profile', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You are now not following {username}.')
    return redirect(url_for('main.profile', username=username))


@main_bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    text = [{'text': f"{request.form['text']}"}]

    return jsonify(
        {
            'text': translate(text, request.form['dest_language'])
        }
    )


@main_bp.route('/<username>/followers')
@login_required
def followers_list(username):
    page = request.args.get('page', 1, type=int)

    if current_user.username == username:
        followers = current_user.followers.paginate(page, current_app.config['USERS_PER_PAGE'], False)
    else:
        followers = User.query.filter_by(username=username).first_or_404().followers.paginate(page, current_app.config['USERS_PER_PAGE'], False)

    next_url = url_for('main.followers_list', page=followers.next_num) if followers.has_next else None
    prev_url = url_for('main.followers_list', page=followers.prev_num) if followers.has_prev else None
    return render_template('main/followers.html', followers=followers.items, prev_url=prev_url, next_url=next_url, username=username)


@main_bp.route('/<username>/followed')
@login_required
def followed_list(username):
    page = request.args.get('page', 1, type=int)

    if current_user.username == username:
        followed = current_user.followed.paginate(page, current_app.config['USERS_PER_PAGE'], False)
    else:
        followed = User.query.filter_by(username=username).first_or_404().followed.paginate(page, current_app.config['USERS_PER_PAGE'], False)

    next_url = url_for('main.followed_list', page=followed.next_num) if followed.has_next else None
    prev_url = url_for('main.followed_list', page=followed.prev_num) if followed.has_prev else None
    return render_template('main/followed.html', followed=followed.items, prev_url=prev_url, next_url=next_url, username=username)


@main_bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page, current_app.config['POSTS_PER_PAGE'])

    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total['value'] > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) if page > 1 else None

    return render_template('main/search.html', title='Search', posts=posts, next_url=next_url, prev_url=prev_url)
