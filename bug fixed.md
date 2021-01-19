## requirements.txt
Error when running pip install -r requirements.txt
-  19 **MarkupSafe==1.0**
  
_Change to:_ 
**MarkupSafe==1.1.1**

##app.py
- homepage()
  
  ```python
    likes = [like.message_id for like in db.session.query(Likes).filter(Likes.user_id == g.user.id).all()]
    return render_template('home.html', messages=messages , likes=likes)
  ```


