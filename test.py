from orm_lite.base import Base
import sqlite3


class User(Base):
    __tablename__ = 'users'

    id = ('int', 'pk')
    username = ('char(255)', 'not_required')


class Post(Base):
    __tablename__ = 'posts'

    id = ('int', 'pk')
    post = ('varchar(255)', 'not_required')
    user_id = ('int', 'fk', 'users.id')


conn = sqlite3.connect('test.db')
u = User(connection=conn)
if u.is_exists():
    u.drop()
u.create()

p = Post(connection=conn)
if p.is_exists():
    p.drop()
p.create()

u(id=1, username='John').add()
u(id=2, username='Max').add()
u(id=3, username='Ivan').add()
u(id=4, username='Max').add()
print(u().select_all())
print(u(username='Max').select_all())
print(u().select('username'))

u(id=1).update(username='Tom')
print(u().select_all())

p(id=1, post='Post1', user_id=1).add()
p(id=2, post='Post2', user_id=1).add()
print(p().select_all())
print(p().select('id', 'post', 'users.username'))

u().update(username='Tom')
print(u().select_all())

u(id=2).delete()
print(User(connection=conn).select_all())

u().delete()
print(User(connection=conn).select_all())