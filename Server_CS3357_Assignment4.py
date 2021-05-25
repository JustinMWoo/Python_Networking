# CS 3357 Assignment #4
# Name: Justin Woo
# Student number: 250860368

from socket import *
import os.path
from email.utils import parsedate_to_datetime

# Define a constant for our buffer size and server port

BUFFER_SIZE = 1024
SERVER_PORT = 15000


def process_message(message):
    """
    Takes a message that was read in from the socket and determines if the correct html version is used,
    the request is a GET request and if the file specified in the GET request exists. Then generates the appropriate
    header for the returned message.
    :param message: The message to be processed
    :return: A tuple with the header in index 0 and the file name in index 1
    """
    # split the header lines
    split_message = message.split("\r\n")

    # split the request line
    request_line = split_message[0].split(" ", 2)

    header_line = ""

    # if the length of the request line is not formatted for GET then return a 501 message
    if len(request_line) < 3:
        header_line = "HTTP/1.1 501 Method Not Implemented\r\n"
        file_path = "./501.html"
        return header_line, file_path

    request = request_line[0]
    file_path = request_line[1]

    if file_path[0] == "/":
        file_path = "." + file_path  # Make the file path relative
    version = request_line[2]

    # set the message header and file to send if the version is not HTTP/1.1
    if version != "HTTP/1.1":
        header_line = "HTTP/1.1 505 Version Not Supported.\r\n"

        # Get HTML file lines to send
        file_path = "./505.html"

    # set the message header and file to send depending on if the file requested in the GET exists
    elif request == "GET":
        if os.path.isfile(file_path):  # check if requested file exists
            # check for conditional GET
            for line in split_message:
                if "If-Modified-Since:" in line:
                    split_line = line.split(" ", 1)
                    rcv_date = parsedate_to_datetime(split_line[1]).timestamp()
                    # check file's last modified date
                    last_modified = os.path.getmtime(file_path)

                    if rcv_date < last_modified:  # if the file has been modified
                        header_line = "HTTP/1.1 200 OK\r\n"  # Message Header
                    else:  # if the file has not been modified
                        header_line = "HTTP/1.1 304 Not Modified\r\n"  # Message Header
                        file_path = "./304.html"
                    break
                else:  # there is no conditional get
                    header_line = "HTTP/1.1 200 OK\r\n"  # Message Header
        else:
            file_path = "./404.html"
            header_line = "HTTP/1.1 404 Not Found\r\n"  # Message Header

    else:  # method other than GET is requested
        header_line = "HTTP/1.1 501 Method Not Implemented\r\n"
        file_path = "./501.html"

    # Add the length and type of the content to the header
    header_line += "Content-Length: " + str(os.path.getsize(file_path)) + "\r\n"
    if ".jpg" in file_path or ".jpeg" in file_path:
        header_line += "Content-Type: image/jpeg\r\n\r\n"
    elif ".gif" in file_path:
        header_line += "Content-Type: image/gif\r\n\r\n"
    else:
        header_line += "Content-Type: text/html\r\n\r\n"

    return header_line, file_path


def main():
    # start up server
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind(('', SERVER_PORT))
    server_socket.listen(1)

    print("The server is now active.")
    while True:
        # connect with client
        connection_socket, addr = server_socket.accept()
        rcv_message = connection_socket.recv(BUFFER_SIZE).decode()
        print("Client connected...")

        # print the request from the client for debugging
        # print(rcv_message)

        # process incoming request to see if it is a GET request
        processed_message = process_message(rcv_message)
        header = processed_message[0]
        file = processed_message[1]

        # prints the header to be sent to the client for debugging
        # print("------------------")
        # print(header)

        print("Sending file \"" + file + "\"")
        connection_socket.send(header.encode())
        open_file = open(file, "rb")

        while True:
            file_text = open_file.readline(BUFFER_SIZE)
            if not file_text:
                break
            connection_socket.send(file_text)

        open_file.close()
        connection_socket.close()
        print("Client disconnected...\n")


main()
