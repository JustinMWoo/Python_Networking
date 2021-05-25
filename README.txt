The timeout for the balancer is set to 300sec by default in a constant.
The html files should be in the same folder as the server.
The file for testing performance is set to "test.jpg" by default as a constant in the load balancer. 

Balancer port: 14000
Server port: 15000

Balancer should be run as follows:
py Balancer_CS3357_Assignment4.py http://localhost:15000 http://localhost:15001

The server provided has a port of 15000 and the port can be changed through the constant in the server file
Each folder that a server is located in must have the html files and test.jpg
