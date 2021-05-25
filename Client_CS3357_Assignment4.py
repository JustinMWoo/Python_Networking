# CS 3357 Assignment #4
# Name: Justin Woo
# Student number: 250860368

from socket import *
import argparse
import sys
from urllib.parse import urlparse

# Define a constant for our buffer size

BUFFER_SIZE = 1024


def generate_get_message(path_name, server_name, port_num):
    """
    Generates the GET message to be sent to a server using the inputted server name and path name
    :param port_num: The port of the server to connect to
    :param path_name: The path for the file to get
    :param server_name: The name of the server to connect to
    :return: The message that is to be sent to the server
    """
    message = "GET " + path_name + " HTTP/1.1\r\n"
    message += "Host: " + server_name + ":" + str(port_num) + "\r\n\r\n"
    return message


def write_to_file(path_name, client_socket):
    """
    Reads from the socket and writes the contents of the returned file into a file on the client's system
    :param path_name: The path of the file requested
    :param client_socket: The socket to read from
    :return:
    """
    file = path_name.split("/")
    file = file[len(file) - 1]

    rcv_message = "".encode()

    # receive and concatenate the message together
    while True:
        new_msg = client_socket.recv(BUFFER_SIZE)

        if not new_msg:
            break
        rcv_message += new_msg

    # split the header from the message
    message_split = rcv_message.split("\r\n\r\n".encode(), 1)

    # print statement for the header for debugging
    # print(message_split[0].decode())

    print("------------")

    # if 200 message is not received then print the message
    status_line = message_split[0].split("\r\n".encode(), 1)[0]
    if status_line.decode().find("200") == -1:
        print(rcv_message.decode())
        if status_line.decode().find("301") != -1:  # if 301 message then return new request
            location_line = message_split[0].split("\r\n".encode(), 1)[1]
            processed = process_301(location_line.decode())
            return processed
        else:
            return

    # write the contents of the message to the file
    write_file = open(file, 'wb')
    write_file.write(message_split[1])
    print("File downloaded")
    write_file.close()
    return


def process_301(location_message):
    """
    processes the location line of the 301 message to get the filename, host and port
    :param location_message: the location line of a 301 message
    :return: file_name at index 0, host at index 1, port at index 2
    """
    # remove "location:" from the beginning of the message
    location_message = location_message.split(" ", 1)[1]
    try:
        parsed_url = urlparse(location_message)
        if ((parsed_url.scheme != 'http') or (parsed_url.port == None) or (parsed_url.path == '') or (
                parsed_url.path == '/') or (parsed_url.hostname == None)):
            raise ValueError
        host = parsed_url.hostname
        port = parsed_url.port
        file_name = parsed_url.path
    except ValueError:
        print('Error:  Invalid URL.  Enter a URL of the form:  http://host:port/file')
        sys.exit(1)

    return file_name, host, port


def main():
    proxy_status = False
    proxy_name = ""
    proxy_port = ""

    # Check command line arguments to retrieve a URL.

    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="URL to fetch with an HTTP GET request")
    parser.add_argument("-proxy", help="proxy server (cache)")
    args = parser.parse_args()

    # Check the URL passed in and make sure it's valid.  If so, keep track of
    # things for later.

    try:
        parsed_url = urlparse(args.url)
        if ((parsed_url.scheme != 'http') or (parsed_url.port == None) or (parsed_url.path == '') or (
                parsed_url.path == '/') or (parsed_url.hostname == None)):
            raise ValueError
        host = parsed_url.hostname
        port = parsed_url.port
        file_name = parsed_url.path
    except ValueError:
        print('Error:  Invalid URL.  Enter a URL of the form:  http://host:port/file')
        sys.exit(1)

    # check for proxy argument in command line
    if args.proxy:
        proxy_status = True
        args.proxy = str(args.proxy)
        proxy_split = args.proxy.split(":")
        proxy_name = proxy_split[0]
        proxy_port = proxy_split[1]

    # worse method for processing the arguments
    # arguments = len(sys.argv)
    # if arguments == 4:
    #     if "-proxy" in sys.argv:
    #         i = sys.argv.index("-proxy")
    #         proxy = sys.argv[i+1].split(":")
    #         proxy_name = proxy[0]
    #         proxy_port = proxy[1]
    #         proxy_status = True
    #     else:
    #         print("Bad Arguments. Exiting...")
    #         return -1
    # elif arguments != 2:
    #     print("Invalid number of arguments (this client takes either one argument or three)")
    #     return -1

    # if proxy_status:
    #     server = sys.argv[3].split(":")
    #     server_name = server[0]
    #     server_port = server[1]
    # else:
    #     server = sys.argv[1].split(":")
    #     server_name = server[0]
    #     server_port = server[1]
    # path_name = input('Input file name: ')

    # open client socket and attempt connection to the server
    try:
        client_socket = socket(AF_INET, SOCK_STREAM)
        if not proxy_status:
            # no proxy provided
            client_socket.connect((host, int(port)))
        else:
            # proxy provided
            client_socket.connect((proxy_name, int(proxy_port)))
    except ConnectionRefusedError:
        print('Error:  That host or port is not accepting connections.')
        sys.exit(1)

    # generate the request that is to be sent to the proxy or the server directly
    request = generate_get_message(file_name, host, port)
    print("Sending request ...")

    # print the request that is sent to the server for debugging
    # print(request)

    client_socket.send(request.encode())

    forward = write_to_file(file_name, client_socket)

    client_socket.close()

    if forward is not None:  # then 301 message
        try:
            # Connect to the actual host
            client_socket = socket(AF_INET, SOCK_STREAM)
            client_socket.connect((forward[1], int(forward[2])))

        except ConnectionRefusedError:
            print('Error:  That host or port is not accepting connections.')
            sys.exit(1)

        # send request to new host
        message = generate_get_message(forward[0], forward[1], forward[2])
        client_socket.send(message.encode())

        write_to_file(file_name, client_socket)

        client_socket.close()


main()
