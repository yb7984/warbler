"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from csv import DictReader
from unittest import TestCase
from sqlalchemy.exc import IntegrityError , InvalidRequestError
from models import db, User, Message, Follows , Likes
from flask import session, request, g

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app,CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True

# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Don't req CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False

db.drop_all()
db.create_all()

class UserViewTestCase(TestCase):
    """Test User View."""

    def setUp(self):
        """Clear the tables"""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        u1 = User.signup(
            email="test@test.com",
            username="testuser",
            password="password" ,
            image_url=None
        )

        u2 = User.signup(
            email="test2@test.com" ,
            username="testuser2" ,
            password="password" ,
            image_url=None
        )

        db.session.add_all([u1 , u2])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id

    def tearDown(self):
        """Clean up any faulted transaction."""
        db.session.rollback()

    def login(self):
        """login user"""
        # login as u1
        with self.client.session_transaction() as change_session:
            change_session[CURR_USER_KEY] = self.u1_id

    def logout(self):
        """logout user"""
        with self.client.session_transaction() as change_session:
            if CURR_USER_KEY in change_session:
                del change_session[CURR_USER_KEY]


    def test_homepage(self):
        """homepage"""

        with self.client as client:
            #not login yet
            #front page
            resp = client.get('/')
            html = resp.get_data(as_text=True)

            #show front page have link to sign up or login
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h4>New to Warbler?</h4>' , html)

            self.login()

            resp = client.get('/')
            html = resp.get_data(as_text=True)

            #show front page have link to sign up or login
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser' , html)

    def test_signup(self):
        """signup"""

        with self.client as client:
            #signup page
            resp = client.get('/signup')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Join Warbler today.' , html)

            resp = client.post('/signup' , data={
                "username":"test1" ,
                "email":"test1@testtest.com" ,
                "password":"testpassword" ,
                "image_url":""} ,
                follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@test1' , html)
            self.assertIsNotNone(session[CURR_USER_KEY])

            self.logout()

            # username & email conflict
            resp = client.post('/signup' , data={
                "username":"test1" ,
                "email":"test1@testtest.com" ,
                "password":"testpassword" ,
                "image_url":""} ,
                follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Username already taken' , html)

    def test_login(self):
        """login"""
        with self.client as client:
            #login page
            resp = client.get('/login')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Welcome back.' , html)

            #login in as u1
            resp = client.post('/login' , 
                data={"username":"testuser" , "password":"password"} ,
                follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser" , html)
            self.assertEqual(session[CURR_USER_KEY] , self.u1_id)

            self.logout()

            #login in as u1, wrong password
            resp = client.post('/login' , 
                data={"username":"testuser" , "password":"password1"} ,
                follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials." , html)
            self.assertNotIn(CURR_USER_KEY , session)


    def test_users(self):
        """users"""
        with self.client as client:
            #users
            resp = client.get('/users')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="card user-card">' , html)

            #search
            resp = client.get('/users?q=t')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser' , html)

    def test_users_show(self):
        """users_show"""
        with self.client as client:
            #users_show
            resp = client.get(f'/users/{self.u1_id}')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser' , html)
            self.assertNotIn('Delete Profile' , html)
            self.assertNotIn('Edit Profile' , html)

            self.login()
            resp = client.get(f'/users/{self.u1_id}')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser' , html)
            self.assertIn('Delete Profile' , html)
            self.assertIn('Edit Profile' , html)

            self.logout()


    def test_users_following(self):
        """users_following"""
        with self.client as client:
            #show_following
            resp = client.get(f'/users/{self.u1_id}/following')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

            self.login()

            resp = client.get(f'/users/{self.u1_id}/following')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser' , html)
            self.assertIn('Delete Profile' , html)
            self.assertIn('Edit Profile' , html)

            #not login user, not showing edit and delete profile
            resp = client.get(f'/users/{self.u2_id}/following')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser' , html)
            self.assertNotIn('Delete Profile' , html)
            self.assertNotIn('Edit Profile' , html)

            self.logout()
            
    def test_users_followers(self):
        """users_following"""
        with self.client as client:
            #show_followers
            resp = client.get(f'/users/{self.u1_id}/followers')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

            self.login()

            resp = client.get(f'/users/{self.u1_id}/followers')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser' , html)
            self.assertIn('Delete Profile' , html)
            self.assertIn('Edit Profile' , html)

            #not login user, not showing edit and delete profile
            resp = client.get(f'/users/{self.u2_id}/followers')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser' , html)
            self.assertNotIn('Delete Profile' , html)
            self.assertNotIn('Edit Profile' , html)

            self.logout()
            
    def test_add_follow(self):
        """add_follow & stop following"""
        with self.client as client:
            resp = client.post(f'/users/follow/{self.u2_id}' , 
                follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized." , html)
            self.assertNotIn(CURR_USER_KEY , session)

            resp = client.post(f'/users/stop-following/{self.u2_id}' , 
                follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized." , html)
            self.assertNotIn(CURR_USER_KEY , session)


            self.login()
            #add to following
            resp = client.post(f'/users/follow/{self.u2_id}' , 
                follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@testuser2' , html)

            #stop following
            resp = client.post(f'/users/stop-following/{self.u2_id}' , 
                follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('@testuser2' , html)

            self.logout()


    def test_profile(self):
        """profile"""
        with self.client as client:
            #profile
            resp = client.get(f'/users/profile' , follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.' , html)

            self.login()

            #get
            resp = client.get(f'/users/profile')
            html = resp.get_data(as_text=True)
            self.assertIn('testuser' , html)

            #post update success
            resp = client.post(
                '/users/profile'  ,
                data={
                    "username":'testuser1' ,
                    "password":'password' ,
                    "email":'testtest@test.com',
                    "image_url":'' ,
                    "header_image_url":'' ,
                    "bio": 'bio information'

                } , 
                follow_redirects=True
                )
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('testuser1' , html)

            #post update wrong password
            resp = client.post(
                '/users/profile'  ,
                data={
                    "username":'testuser1' ,
                    "password":'password1' ,
                    "email":'testtest@test.com',
                    "image_url":'' ,
                    "header_image_url":'' ,
                    "bio": 'bio information'

                } , 
                follow_redirects=True
                )
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.' , html)
            
            #post update username conflict
            resp = client.post(
                '/users/profile'  ,
                data={
                    "username":'testuser2' ,
                    "password":'password' ,
                    "email":'testtest@test.com',
                    "image_url":'' ,
                    "header_image_url":'' ,
                    "bio": 'bio information'
                } , 
                follow_redirects=True
                )
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Username or Email already taken' , html)

    def test_delete_user(self):
        """delete_user"""
        with self.client as client:
            #profile
            resp = client.post(f'/users/delete' , follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.' , html)

            self.login()

            resp = client.post(f'/users/delete' , follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(CURR_USER_KEY , session)

    

            