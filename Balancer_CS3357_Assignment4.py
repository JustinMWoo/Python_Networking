# CS 3357 Assignment #4
# Name: Justin Woo
# Student number: 250860368

from socket import *
import argparse
import sys
import time
from urllib.parse import urlparse
from random import randint

BALANCER_PORT = 14000
PERFORMANCE_FILE = "test.jpg"  # file name for the performance tests
BUFFER_SIZE = 1024
TIMEOUT = 300


def performance_test(hosts, ports):
    """
    Takes a list of hosts and a list of ports, requests the PERFORMANCE_FILE from each server and times each request
    :param hosts: list of hosts to connect to
    :param ports: list of ports for the hosts
    :return: a tuple with the hosts at index 0 and the ports at index 1 sorted in order of performance
    """
    print("Running performance tests...")
    times = []

    # time how long it takes for each host to transfer the test file to the balancer
    for host, port in zip(hosts, ports):
        try:
            client_socket = socket(AF_INET, SOCK_STREAM)
            client_socket.connect((host, int(port)))
        except ConnectionRefusedError:
            print('Error:  That host or port is not accepting connections.')  # ignore this host
            hosts.remove(host)
            ports.remove(port)
            continue

        message = "GET " + PERFORMANCE_FILE + " HTTP/1.1\r\n"
        message += "Host: " + host + ":" + str(port) + "\r\n\r\n"

        start = time.time()
        client_socket.send(message.encode())

        rcv_message = "".encode()
        while True:
            new_msg = client_socket.recv(BUFFER_SIZE)

            if not new_msg:
                break
            rcv_message += new_msg

        end = time.time()
        times.append(end-start)
        print("Host: " + host + ":" + str(port) + " Time: " + str(end-start))
        client_socket.close()

    if len(hosts) < 1:
        print("All hosts have been closed")
        sys.exit(1)

    # sort the two lists in the order of the time
    sorted_hosts = [sort for _, sort in sorted(zip(times, hosts), reverse=True)]
    sorted_ports = [sort for _, sort in sorted(zip(times, ports), reverse=True)]
    return sorted_hosts, sorted_ports


def pick_host(hosts, ports):
    """
    Generates a random number to select a host depending on the speed of the server

    :param hosts: the hosts available to the balancer
    :param ports: the ports of the hosts
    :return: a tuple with the selected host in index 0 and port in index 1
    """
    x = 1
    total = 0
    while x <= len(hosts):  # get the sum of the numbers up to the number of hosts
        total += x
        x += 1

    random_server = randint(1, total)  # generate a random number between 1 and the total

    # use the random number to select a server depending on the speed of the server
    # e.g. with 3 servers the slowest server will get 1, middle server will get 2-3 and the fastest server will get 4-6
    i = 1
    cur_total = i
    while i <= len(hosts):
        if random_server <= cur_total:
            # print(random_server)
            print("Selected host: " + hosts[i-1] + ":" + str(ports[i-1]))
            return hosts[i-1], ports[i-1]

        i += 1
        cur_total += i


def get_file_path(message):
    """
    Splits the received message and returns the file path
    :param message: The message to be processed
    :return: file path in the message
    """
    # split the header lines
    split_message = message.split("\r\n")

    # split the request line
    request_line = split_message[0].split(" ", 2)
    file_path = request_line[1]

    return file_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", action='append', nargs='+', help="URL to fetch with an HTTP GET request")
    args = parser.parse_args()

    i = 0
    hosts = []
    ports = []
    try:
        arg = args.url[0]
        while i < len(arg):
            parsed_url = urlparse(arg[i])
            i += 1
            if (parsed_url.scheme != 'http') or (parsed_url.port == None) or (parsed_url.hostname == None):
                raise ValueError
            hosts.append(parsed_url.hostname)  # list of the hosts
            ports.append(parsed_url.port)  # list of the ports
    except ValueError:
        print('Error:  Invalid URL.  Enter a URL of the form:  http://host:port')
        sys.exit(1)

    # run the performance test
    servers = performance_test(hosts, ports)

    while True:
        # set up for clients
        balancer_socket = socket(AF_INET, SOCK_STREAM)
        balancer_socket.bind(('', BALANCER_PORT))
        balancer_socket.listen(1)
        balancer_socket.settimeout(TIMEOUT)

        print("The balancer is now active.")
        try:
            while True:
                # connect with client
                connection_socket, addr = balancer_socket.accept()
                balancer_socket.settimeout(TIMEOUT)  # reset the timeout
                rcv_message = connection_socket.recv(BUFFER_SIZE).decode()

                print("Client connected...")
                file_path = get_file_path(rcv_message)

                selected_host = pick_host(servers[0], servers[1])
                # print(selected_host[0], selected_host[1])

                # generate the 301 message to direct client to selected server
                message = "301 Moved Permanently\r\n"
                message += "Location: http://" + selected_host[0] + ":" + str(selected_host[1]) + file_path + "\r\n\r\n"
                connection_socket.send(message.encode())

                # send file 301.html
                open_file = open("301.html", "rb")
                while True:
                    file_text = open_file.readline(BUFFER_SIZE)
                    if not file_text:
                        break
                    connection_socket.send(file_text)

                open_file.close()

                connection_socket.close()
                print("Client disconnected...\n")
        except Exception as e:  # if timeout then re run the performance test
            servers = performance_test(hosts, ports)


main()
