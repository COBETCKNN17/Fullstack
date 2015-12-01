from flask import Flask, render_template, redirect, url_for, request, flash

from flask import jsonify


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

from functools import wraps

app = Flask(__name__)

# Oauth - save CLIENT_ID
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Bullion Catalog"

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    '''Create random string for login, state token; stored in login_session dictionary.'''

    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token

    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    # access_token = login_session.get('credentials')
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


def createUser(login_session):
    '''Given login session, creates a new user account.
    Returns user.id'''
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    '''Given a user_id, returns user info'''
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    '''Give an email, returns user.id found in the database'''
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    '''Disconnect function. On logout, the user is redirected to the main page'''
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("logged out")
        return redirect(url_for('showCategories'))
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        flash("log out failed")
        return redirect(url_for('showCategories'))


# Connect to database
engine = create_engine('sqlite:///bullion.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Flask methods
@app.route('/')
# Main page - this page shows the bullion categories
@app.route('/categories/')
def showCategories():
    '''This function generates the main page, '/categories'. '''
    categories = session.query(Category).all()
    if 'user_id' not in login_session:
        return render_template('categories.html', categories=categories,
                               login_session=login_session)
    else:
        return render_template('categories.html', categories=categories,
                               login_session=login_session)


# Create new category
@app.route('/categories/new/', methods=['GET', 'POST'])
def newCategory():
    '''Create new Category '''

    if request.method == 'POST':
        if request.form['name']:
            newCategory = Category(name=request.form['name'])
            session.add(newCategory)
            session.commit()
            flash("New category created!")
            return redirect(url_for('showCategories'))
    else:
        return render_template('newCategory.html')


# edit existing category
@app.route('/categories/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    '''Edit new Category '''

    editedCategory = session.query(Category).get(category_id)
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
        session.add(editedCategory)
        session.commit()
        flash("Category Edited!")
        return redirect(url_for('showCategories'))
    else:
        return render_template('editCategory.html', category_id=category_id,
            editedCategory=editedCategory)

# delete existing category
@app.route('/categories/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    '''Delete existing Category '''

    deletedCategory = session.query(Category).get(category_id)
    if request.method == 'POST':
        session.delete(deletedCategory)
        session.commit()
        flash("Category has been deleted")
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteCategory.html',category_id=category_id,
            deletedCategory=deletedCategory)


# list coins inside each category
@app.route('/categories/<int:category_id>/')
def showCoins(category_id):
    '''Show coins saved in bullion.db - created via sqlalchemy '''
    category = session.query(Category).get(category_id)
    items = session.query(Item).filter_by(category_id=category.id)
    if 'user_id' not in login_session:
        return render_template('category.html',category=category,
            items=items, login_session=login_session)
    else:
        return render_template('category.html', category=category,
            items=items, login_session=login_session)


# add new coin to category
@app.route('/categories/<int:category_id>/new/', methods=['GET', 'POST'])
def newCoin(category_id):
    '''Create new coin function - will create record in bullion.db '''
    category = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            mint="mint",
            image=request.form['image'],
            description=request.form['description'],
            category_id=category_id)
        session.add(newItem)
        session.commit()
        flash("New has been created")
        return redirect(url_for('showCoins', category_id=category_id))
    else:
        return render_template('newCoin.html', category_id=category_id)


# edit an existing coin
@app.route('/categories/<int:category_id>/<int:item_id>/edit',methods=['GET', 'POST'])
def editCoin(category_id, item_id):
    '''Edit a coin in bullion.db '''
    category = session.query(Category).get(category_id)
    editedItem = session.query(Item).get(item_id)
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['mint']:
            editedItem.ingredients = request.form['mint']
        if request.form['image']:
            editedItem.price = request.form['image']
        if request.form['description']:
            editedItem.image_url = request.form['description']
        session.add(editedItem)
        session.commit()
        flash("Coin has been edited")
        return redirect(url_for('showCoins', category_id=category_id))
    else:
        return render_template('editCoin.html',category_id=category_id,
            item_id=item_id,item=editedItem)


# delete an existing coin
@app.route('/categories/<int:category_id>/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteCoin(category_id, item_id):
    '''Delete a coin in bullion.db '''
    category = session.query(Category).get(category_id)
    deletedItem = session.query(Item).get(item_id)
    if request.method == 'POST':
        session.delete(deletedItem)
        session.commit()
        flash("Item Deleted!")
        return redirect(url_for('showCoins', category_id=category_id))
    else:
        return render_template('deleteCoin.html',category_id=category_id,
            item_id=item_id, deletedItem=deletedItem)


# JSON API Endpoint
@app.route('/categories/items/JSON')
def allItemsJSON():
    items = session.query(Item).all()
    return jsonify(SupplyItems=[i.serialize for i in items])


@app.route('/categories/<int:category_id>/items/JSON')
def supplyItemJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(SupplyItems=[i.serialize for i in items])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
