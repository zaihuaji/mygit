# A first Python script
import sys
import mysql.connector
print(sys.platform)
print(2 ** 100)
x = 'Spam!'
print(x * 8)
y='1'

if type(x) == int:
   print x
else:
   print y 

cnx = mysql.connector.Connect()

