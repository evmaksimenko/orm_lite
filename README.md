# orm_lite
Simple ORM library for SQLite.

Supports the following operations:
- creation / deletion of tables;
- records insert / update ;
- select with required columns;
- support for foreign key and auto join.

## Requirements
The project requires python3, no additional libraries are required.

## Installation
Clone the repository with the following command:

**git@github.com:evmaksimenko/orm_lite.git**

or 

**https://github.com/evmaksimenko/orm_lite.git**

Then import the orm_lite.py library into your project.

## Using
Import Base class from orm_lite.

**from orm_lite import Base**

### Tables definition
The table is defined in a class inherited from the class **orm_lite.Base**.

In the class, you must specify the table name in a special variable **\_\_tablename__**.
After that, you need to describe the table columns.

**COLUMN_NAME = (TYPE, PARAMS)**

The type can be of type 'int', 'text', 'char (length)', 'varchar (length)'.

Valid parameters:
- "pk" is the primary key.
- "required" - required field (not null).
- "not_required" - optional field (by default) - it is possible not to specify.
- "fk" is the foreign key. After it, you must specify a link to the field in another table,
e.g. "users.id"

Examples:

class User

    class User(Base):
        __tablename__ = 'users' # table 'users'

    id = ('int', 'pk')          # primary key of type int
    username = ('char(255)', 'not_required') 

class Post
 
    class Post(Base):   
        __tablename__ = 'posts'

    id = ('int', 'pk')
    post = ('varchar(255)', 'not_required')
    user_id = ('int', 'fk', 'users.id') # foreign key on the id field of the users table 

When accessing a table, you must specify a connection to the database as a parameter.

    conn = sqlite3.connect('test.db')
    User(connection=conn)."method" 

You can also use the assignment variably with its call.
    
    u = User(connection=conn)
    u."method"

###Working with tables
Check the existence of the table

    u.is_exists() # true if table exists 

Delete table

    u.drop()

Create table

    u.create()

If the table already exists, nothing will happen.

Example:

    if u.is_exists():
        u.drop()
    u.create()
 
###Working with records
Add an record to the table

    u(id=1, username='John').add() # All required fields must be initialized

or

    User(id=1, username='John', connection=conn).add()


Update record

    u(id=1).update(username='Tom')  # Update specific record
    u().update(username='Oh, No!')  # Update all records in table
    
Select all records from the table 

    u().select_all()

The method returns a list of tuples, such as [(1, 'John'), ...]. If the table has 
foreign keys the selection will also be from the linked table.

Select all records in the table with field filtering.

    u(username='Max').select_all()
    
Select specific fields:

    u().select('username') # you must list all field names 
    p().select('id', 'post', 'users.username') # Simple names refer to the current table
    # you can use dot notation

Delete record:

    u(id=2).delete()    # Specific record
    u().delete()        # All records 
    
An example of use is given in the file ** test.py **