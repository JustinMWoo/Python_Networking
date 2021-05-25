# CS 3357 Assignment #3
# Name: Justin Woo
# Student number: 250860368

from socket import *
import time
import os.path

# Define a constant for our buffer size the port for the cache and the expiration timer on the files

BUFFER_SIZE = 1024
CACHE_PORT = 10000
EXPIRATION_TIME = 60


def write_to_file(path_name, server_socket):
    """
    Takes input from the server and writes the contents to a file if no error is returned. If a 304 is returned, then
    generates and returns a header. If 404 is returned then deletes the file on the cache if it exists and
    returns the header. If any other message other than 200 is received, then returns the whole message. If a 200
    is received, then saves the file to the cache and returns the same header that was received.
    :param path_name: The path of the file
    :param server_socket: The connection socket of the client
    :return: the header to be returned to the client
    """
    rcv_message = "".encode()

    # receive and concatenate the message together
    while True:
        new_msg = server_socket.recv(BUFFER_SIZE)

        if not new_msg:
            break
        rcv_message += new_msg

    # split the header from the message
    message_split = rcv_message.split("\r\n\r\n".encode(), 1)

    # print statement for the header for debugging
    # print(message_split[0].decode())

    print("------------")

    # split the first line of the header and check for returned message type
    status_line = message_split[0].split("\r\n".encode(), 1)[0]

    # if a 304 is returned by the server, then generate the appropriate header and return
    if not status_line.decode().find("304") == -1:
        header = "HTTP/1.1 200 OK\r\n"
        header += "Content-Length: " + str(os.path.getsize(path_name)) + "\r\n"
        if ".jpg" in path_name or ".jpeg" in path_name:
            header += "Content-Type: image/jpeg\r\n\r\n"
        elif ".gif" in path_name:
            header += "Content-Type: image/gif\r\n\r\n"
        else:
            header += "Content-Type: text/html\r\n\r\n"
        return header

    # if 404 is returned by the server then delete file on cache if it exists and return the entire message
    if not status_line.decode().find("404") == -1:
        if os.path.isfile(path_name):
            os.remove(path_name)
        return rcv_message.decode()

    # if anything other than 304, 404 or 200 is received then return the entire message
    if status_line.decode().find("200") == -1:
        return rcv_message.decode()

    # create the directory if it does not exist
    if not os.path.exists(os.path.dirname(path_name)):
        os.makedirs(os.path.dirname(path_name))

    # write the contents of the message to the file
    write_file = open(path_name, 'wb')
    write_file.write(message_split[1])
    print("File downloaded")
    write_file.close()

    # return the header and re-add the end line characters
    return message_split[0].decode() + "\r\n\r\n"


def forward_message(message):
    """
    Takes the message provided by the client and forwards it to the server
    :param message: message received from the client
    :return: a tuple with the path of the file at index 0 and the header to be sent at index 1 or returns -1 if no host
            is provided by the client
    """
    # split the header lines
    split_message = message.split("\r\n")

    # split the request line
    request_line = split_message[0].split(" ", 2)

    # format the file path
    file_path = request_line[1]
    if file_path[0] == ".":
        file_path = file_path[1:]
    elif not file_path[0] == "/":
        file_path = "/" + file_path

    # get the host that the message will be forwarded to
    host_line = ""
    for line in split_message:
        if "Host: " in line:
            host_line = line
    # if a host line was found then split it into address and port
    if not host_line == "":
        target_host = host_line.split(" ")[1].split(":")
    else:
        # no host provided
        return -1

    # combine the host address and file path to get the file path on the cache
    full_path = target_host[0] + "_" + target_host[1] + file_path

    # if the file already exists on the cache, get the last modified date for conditional get
    if os.path.isfile(full_path):
        last_modified = os.path.getmtime(full_path)
        curr_time = time.time()
        if (last_modified + EXPIRATION_TIME) > curr_time:  # if not expired then send conditional get
            # convert the time to the correct format for HTTP header
            last_modified = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(last_modified))
            # remove the \r\n\r\n at the end of the header to add the conditional line
            message = message.replace("\r\n\r\n", "")
            message += "\r\n" + "If-Modified-Since: " + last_modified + "\r\n\r\n"

    # connect to the server provided in the Host: line of the original request
    try:
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.connect((target_host[0], int(target_host[1])))
    except ConnectionRefusedError:
        print('Error:  That host or port is not accepting connections.')
        header = "523 Origin Is Unreachable"
        return full_path, header

    # send the request to the server
    server_socket.send(message.encode())
    header = write_to_file(full_path, server_socket)

    server_socket.close()
    return full_path, header


def send_file_to_client(connection_socket, header, file_path):
    """
    Sends file to the client if it exists on the cache, otherwise sends only the header
    :param connection_socket: the socket that the client is connected on
    :param header: header to be sent to the client or the entire message to be sent if an error has occurred
    :param file_path: path to the file that is to be sent
    :return:
    """
    connection_socket.send(header.encode())

    # if there is no file then message received from server is not 304 or 200
    if not os.path.isfile(file_path):
        return

    # open the file and send it to the client
    open_file = open(file_path, "rb")

    while True:
        file_text = open_file.readline(BUFFER_SIZE)
        if not file_text:
            break
        connection_socket.send(file_text)

    open_file.close()


def main():
    # start up cache
    cache_socket = socket(AF_INET, SOCK_STREAM)
    cache_socket.bind(('', CACHE_PORT))
    cache_socket.listen(1)

    print("The server is now active.")
    while True:
        # connect with client
        connection_socket, addr = cache_socket.accept()
        rcv_message = connection_socket.recv(BUFFER_SIZE).decode()
        print("Client connected...")

        # print the request from the client for debugging
        # print(rcv_message)

        # process incoming request and forward to the server
        message_result = forward_message(rcv_message)

        # no host provided by the client
        if message_result == -1:
            connection_socket.close()
            print("No host provided. Client disconnected...\n")
            continue

        # send the file and header to the client
        send_file_to_client(connection_socket, message_result[1], message_result[0])

        connection_socket.close()
        print("Client disconnected...\n")


main()
