"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError , InvalidRequestError
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


class UserModelTestCase(TestCase):
    """Test User Model."""

    def setUp(self):
        """Clear the tables"""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

    def tearDown(self):
        """Clean up any faulted transaction."""
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers & no likes
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u.following) , 0)
        self.assertEqual(len(u.likes) , 0)

        # User id should be greater than 0
        self.assertGreater(u.id , 0)

    def test_repr(self):
        """Does the repr method work as expected"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        self.assertEqual(
            u.__repr__() ,
            f"<User #{u.id}: {u.username}, {u.email}>"
            )

    def test_is_following(self):
        """Does is_following & is_followed_by successfully detect when user1 is following user2?"""

        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com" ,
            username="testuser2" ,
            password="HASHED_PASSWORD"
        )

        db.session.add_all([u1 , u2])
        db.session.commit()

        self.assertEqual(u1.is_following(u2) , False)
        self.assertEqual(u2.is_followed_by(u1) , False)

        u1.following.append(u2)
        db.session.commit()

        self.assertEqual(u1.is_following(u2) , True)
        self.assertEqual(u2.is_followed_by(u1) , True)

    def test_signup(self):
        """
        test for signup classmethod
        Does User.signup successfully create a new user given valid credentials?
        Does User.signup fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?
        """


        u = User.signup(
            username='test',
            email='test@test.com',
            password='password' ,
            image_url=None
        )

        db.session.add(u)
        db.session.commit()

        #successful , id should be greater than 0
        self.assertGreater(u.id , 0)

        #duplicate user
        u1 = User.signup(
            username='test',
            email='test@test.com',
            password='password' ,
            image_url=None
        )

        db.session.add(u1)

        with self.assertRaises(IntegrityError) as cm:
            db.session.commit()

        self.assertIn("psycopg2.errors.UniqueViolation" , str(cm.exception))


    def test_authenticate(self):
        """
        test for authenticate classmethod
        Does User.authenticate successfully return a user when given a valid username and password?
        Does User.authenticate fail to return a user when the username is invalid?
        Does User.authenticate fail to return a user when the password is invalid?"""


        #signup the user
        u = User.signup(
            username='test',
            email='test@test.com',
            password='password' ,
            image_url=None
        )

        db.session.add(u)
        db.session.commit()


        #successful
        user = User.authenticate(username='test' , password='password')

        self.assertEqual(type(user) , User)

        #username invalid
        user = User.authenticate(username='test1' , password='password')

        self.assertEqual(user , False)

        #password invalid
        user = User.authenticate(username='test' , password='password1')

        self.assertEqual(user , False)

