#import
import random
import pyfiglet
import mysql.connector
from geopy import distance


# Database connection
conn = mysql.connector.connect(
    host='127.0.0.1',
    port=3306,
    database='test1',
    user='root',
    password='12345',
    autocommit=True
)

#eras(energy consumption)
ERAS = {
    'ANCIENT': 1.2,
    'MEDIEVAL': 1.1,
    'MODERN': 1.0,
    'FUTURE': 0.9
}

#get 15 random airports(function)
#get all goals(function)
#create a new game(function)
#getting airport info(function)
#checking goals(function)
#calculate distance(function)
#airports in range(function)
#update game(function)
#game state(function)
