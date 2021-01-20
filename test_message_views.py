"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User , Follows , Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True

# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Don't req CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False

class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        user_id = self.testuser.id
        with self.client as c:
            #not login redirect
            resp = c.get('/messages/new')
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user_id

            resp = c.get('/messages/new')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Add my message!' , html)

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_message_show(self):
        """show a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        user_id = self.testuser.id
        user_id2 = self.testuser2.id

        msg = Message(user_id=user_id , text="test text")
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            #not login redirect
            resp = c.get(f'/messages/{msg.id}')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("Delete", html)

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user_id

            resp = c.get(f'/messages/{msg.id}')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            #own message should have Delete button 
            self.assertIn('Delete' , html)

            #login as other user
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user_id2

            resp = c.get(f'/messages/{msg.id}')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            #not own message should not show Delete button
            self.assertNotIn('Delete' , html)

    def test_messages_destroy(self):
        """destroy a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        user_id = self.testuser.id
        user_id2 = self.testuser2.id

        msg = Message(user_id=user_id , text="test text")
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            #not login redirect, can not delet and redirect to homepage
            resp = c.post(f'/messages/{msg.id}/delete')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

            #login as other user, can not delet and redirect to homepage
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user_id2
            
            resp = c.post(f'/messages/{msg.id}/delete')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, 'http://localhost/')

            #login as owner user, delete successfully and redirect to user page
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user_id

            resp = c.post(f'/messages/{msg.id}/delete')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f'http://localhost/users/{user_id}')

    def test_messages_add_like(self):
        """like a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        user_id = self.testuser.id
        user_id2 = self.testuser2.id

        msg = Message(user_id=user_id , text="test text")
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            #not login redirect, can not like and redirect to homepage
            resp = c.post(f'/users/add_like/{msg.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', html)

            #login as owner user, can not like and redirect to homepage
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user_id
            
            resp = c.post(f'/users/add_like/{msg.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Can not like your own message!', html)


            #login as other user, like successfully and redirect to home page
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user_id2

            #add follow
            follow = Follows(user_being_followed_id=user_id , user_following_id=user_id2)
            db.session.add(follow)
            db.session.commit()

            #like the message
            resp = c.post(f'/users/add_like/{msg.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('btn-primary', html)

            #unlike the message
            resp = c.post(f'/users/add_like/{msg.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('btn-secondary', html)

    def test_messages_show_likes(self):
        """show the list of like messages?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        user_id = self.testuser.id
        user_id2 = self.testuser2.id

        msg = Message(user_id=user_id , text="test text")
        db.session.add(msg)
        db.session.commit()

        like = Likes(message_id=msg.id , user_id=user_id2)
        db.session.add(like)
        db.session.commit()

        with self.client as c:
            #not login redirect, can not like and redirect to homepage
            resp = c.get(f'/users/{user_id}/likes', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', html)

            #login as owner user, not showing this message
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user_id
            
            resp = c.get(f'/users/{user_id}/likes')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('test text', html)


            #login as like user, showing this message
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = user_id2
            
            resp = c.get(f'/users/{user_id2}/likes')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('test text', html)