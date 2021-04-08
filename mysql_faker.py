import datetime
import os
import sys
import getopt
import time
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode
from faker import Faker

# from config import SQL instance connection info, and 
# our database information to connect to the db
SQL_HOST = os.environ.get("SQL_HOST", "127.0.0.1") # Defaults to using localhost/Cloud SQL Proxy
DB_PORT  = os.environ.get("DB_PORT", 3306)
DB_USER  = os.environ.get("DB_USER", None)
DB_PASS  = os.environ.get("DB_PASS", None)
DB_NAME  = os.environ.get("DB_NAME", None)

# configurable defaults for how many variations you want
PRODUCTS = 1000
# EMPLOYEES = 8 # This is number of employees per location, not total

# parsing/handling commandline options
auto_create = False
create_db = False

# Note: By default, each time you run this script, it won't clean the tables out
# If you want to add more data instead of starting fresh, you can pass the flag '-c'
# and it won't clean out the database, but will just add more random values to it
clean_table = False
fullCmdArguments = sys.argv
argumentList = fullCmdArguments[1:]
unixOptions = "hH:P:u:p:d:l:e:ac"
gnuOptions = ["help", "host=", "port=", "user=", "passwd=", "dbname=", "number=", "auto", "dontclean"]

# probably don't NEED to do all this try/catch, but makes it easier to catch what/where goes wrong sometimes
# this chunk is just handling arguments
try:
    arguments, values = getopt.getopt(argumentList, unixOptions, gnuOptions)
except getopt.error as err:
    print (str(err))
    sys.exit(2)

for currentArgument, currentValue in arguments:
    if currentArgument in ("-h", "--help"):
        print ("\nusage: python mysql_faker.py [-h | -P port | -u user | -p passwd | -d dbname | -n number]\nOptions and arguments (and corresponding environment variables):\n-d db\t: database name to connect to or create if it doesn't exist\n-h\t: display this help\n-H addr\t: target MySQL database address. Defaults to 127.0.0.1\n-n num\t: number of products to create\n-P port\t: port to connect to\n-p pwd\t: password for the database user\n-u usr\t: database user to connect with\n-a\t: automatically create the database if it's missing\n-c\t: DON'T clean out the tables before inserting new random data. Default is to start clean\n\nOther environment variables:\nDB_USER\t: database user to connect with. Overridden by the -u flag\nDB_PASS\t: database password. Overridden by the -p flag.\nDB_NAME\t: database to connect to. Overridden by the -d flag.\nSQL_HOST: Remote MySQL database address. Overridden by the -H flag.\nDB_PORT\t: port for MySQL instance. Overridden by the -P flag.")
        sys.exit(0)

    if currentArgument in ("-H", "--host"):
        SQL_HOST = currentValue
    elif currentArgument in ("-P", "--port"):
        DB_PORT = currentValue
    elif currentArgument in ("-u", "--user"):
        DB_USER = currentValue
    elif currentArgument in ("-p", "--passwd"):
        DB_PASS = currentValue
    elif currentArgument in ("-d", "--dbname"):
        DB_NAME = currentValue
    elif currentArgument in ("-n", "--number"):
        PRODUCTS = int(currentValue)
    elif currentArgument in ("-a", "--auto"):
        auto_create = True
    elif currentArgument in ("-c", "--dontclean"):
        clean_table = False

# Make sure that we have all the pieces we must have in order to connect to our db properly
if not DB_USER:
    print ("You have to specify a database user either by environment variable or pass one in with the -u flag.")
    sys.exit(2)
if not DB_PASS:
    print ("You have to specify a database password either by environment variable or pass one in with the -p flag.")
    sys.exit(2)
if not DB_NAME:
    print ("You have to specify a database name either by environment variable or pass one in with the -d flag.")
    sys.exit(2)
if not DB_PORT:
    print ("You have to specify a database port either by environment variable or pass one in with the -P flag.")
    sys.exit(2)


# Wait for our database connection
mydb = None
attempt_num = 0
wait_amount = 1
# backoff_count is the static count for how many times we should try at one
# second increments before expanding the backoff time exponentially
# Once the wait time passes a minute, we'll give up and exit with an error
backoff_count = 5
def connect_database():
    global attempt_num
    global wait_amount
    global mydb
    try:
        mydb = mysql.connector.connect(
            host=SQL_HOST,
            user=DB_USER,
            passwd=DB_PASS,
            port=DB_PORT
        )
    except Error as e:
        attempt_num = attempt_num + 1
        if attempt_num >= backoff_count:
            wait_amount = wait_amount * 2
        print ("Couldn't connect to the MySQL instance, trying again in {} second(s).".format(wait_amount))
        print (e)
        time.sleep(wait_amount)
        if wait_amount > 60:
            print ("Giving up on connecting to the database")
            sys.exit(2)

while mydb == None:
    connect_database()

print("Connected to database successfully")

mycursor = mydb.cursor()

# This is what randomly generates our employee-like data
fake = Faker()

# Attempt to switch to our specified database
# If it doesn't exist, then go through a flow to create it
try:
    mycursor.execute("USE {}".format(DB_NAME))
except Error as e:
    if e.errno == errorcode.ER_BAD_DB_ERROR:
        if auto_create == False:
            u_input = input("Your database doesn't exist, would you like to create it (Y/n)? ")
            if u_input == "Y":
                create_db = True
            else:
                print ("The database doesn't exist and you've chosen to not create it.")
                sys.exit(0)
        else:
            create_db = True

        if create_db:
            try:
                mycursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
                mycursor.execute("USE {}".format(DB_NAME))
            except Error as e:
                print ("Wasn't able to create the database.")
                print (e)
                sys.exit(2)
    else:
        print(e)
        sys.exit(2)


# Fill products table with data
#   `post_author` bigint(20) unsigned NOT NULL DEFAULT 0,
#   `post_date` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
#   `post_date_gmt` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
#   `post_content` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
#   `post_title` text COLLATE utf8mb4_unicode_ci NOT NULL,
#   `post_excerpt` text COLLATE utf8mb4_unicode_ci NOT NULL,
#   `post_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'publish',
#   `comment_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'open',
#   `ping_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'open',
#   `post_password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
#   `post_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
#   `to_ping` text COLLATE utf8mb4_unicode_ci NOT NULL,
#   `pinged` text COLLATE utf8mb4_unicode_ci NOT NULL,
#   `post_modified` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
#   `post_modified_gmt` datetime NOT NULL DEFAULT '0000-00-00 00:00:00',
#   `post_content_filtered` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
#   `post_parent` bigint(20) unsigned NOT NULL DEFAULT 0,
#   `guid` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
#   `menu_order` int(11) NOT NULL DEFAULT 0,
#   `post_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'post',
#   `post_mime_type` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
#   `comment_count` bigint(20) NOT NULL DEFAULT 0,

def create_products():
    if clean_table:
        try:
            mycursor.execute("DELETE FROM wp_posts")
        except Error as e:
            if e.errno != errorcode.ER_BAD_TABLE_ERROR:
                print("There was a problem deleting the existing wp_posts table records.")
                sys.exit(2)

    for product_id in range(1, PRODUCTS + 1):
        post_author = 2
        post_date = datetime.datetime.now().isoformat()
        post_date_gmt = post_date
        post_content = 'FAKE: ' + fake.text(100)
        post_content_filtered = post_content
        post_title = 'FAKE: ' + fake.text(20)
        post_status = 'publish'
        comment_status = 'open'
        ping_status = 'open'
        post_name = fake.md5(False)
        post_modified = post_date
        post_modified_gmt = post_modified
        post_parent = 0
        guid = f'https://eklix.tk/proizvod/{post_name}'
        menu_order = 0
        post_type = 'product'
        post_excerpt = ''
        to_ping = ''
        pinged = ''
        comment_count = 0
        post_mime_type = ''
        post_password = ''
        sql_command = (
            "INSERT INTO wp_posts (post_author, post_date, post_date_gmt, post_content, post_title, post_status, comment_status, ping_status, post_name, post_modified, post_modified_gmt, post_parent, guid, menu_order, post_type, post_excerpt, to_ping, pinged, post_content_filtered, comment_count, post_mime_type, post_password) "
            "VALUES ({}, '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', {}, '{}', '{}')".format(post_author, post_date, post_date_gmt, post_content, post_title, post_status, comment_status, ping_status, post_name, post_modified, post_modified_gmt, post_parent, guid, menu_order, post_type, post_excerpt, to_ping, pinged, post_content_filtered, comment_count, post_mime_type, post_password)
        )
        try:
            mycursor.execute(sql_command)
        except Error as e:
            print (e)

    mydb.commit()


print("Beginning data creation of {} products".format(PRODUCTS))
create_products()
print("Finished creating product records")
