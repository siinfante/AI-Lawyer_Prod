# production.wsgi
import sys
 
sys.path.insert(0,"/var/www/html/flask-app/")
 
from application import application