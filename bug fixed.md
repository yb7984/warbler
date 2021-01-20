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


- messages_destroy()
  
    Bug:Any login user can delete any message. 

    Fix:Make sure check the message user_id with the current login user_id

```python
    if g.user.id != msg.user_id:
        #can only delete your own message
        flash("Access unauthorized.", "danger")
        return redirect("/")
```
