"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from models import db, User, Message, Follows , Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test Message Model."""

    def setUp(self):
        """Clear the tables"""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        self.user = u

    def tearDown(self):
        """Clean up any faulted transaction."""
        db.session.rollback()

    def test_message_model(self):
        """Does basic model work?"""

        u = self.user

        m = Message(
            user_id=u.id ,
            text='test content'
        )

        db.session.add(m)
        db.session.commit()

        self.assertGreater(m.id , 0)
        self.assertEqual(m.user , self.user)
    
    def test_is_liked_by(self):
        """Does the is_liked_by work"""

        u = self.user
        u2 = User(
            email="test2@test.com" ,
            username="testuser2" ,
            password="HASHED_PASSWORD"
        )

        m = Message(
            user_id=u.id ,
            text='test content'
        )

        db.session.add_all([u2 , m])
        db.session.commit()

        #not like 
        self.assertEqual(len(u2.likes) , 0)
        self.assertEqual(len(m.likes_users) , 0)
        self.assertEqual(u2.is_like(m) , False)
        self.assertEqual(m.is_liked_by(u2) , False)

        like = Likes(user_id=u2.id , message_id=m.id)
        db.session.add(like)
        db.session.commit()

        self.assertEqual(len(u2.likes) , 1)
        self.assertEqual(len(m.likes_users) , 1)
        self.assertEqual(u2.is_like(m) , True)
        self.assertEqual(m.is_liked_by(u2), True)