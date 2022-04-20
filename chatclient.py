import socket
import threading
import sys
from queue import Queue

# Server Data Encoding:
# I - Input (Indicates a request for input)
# S - Success (Indicates operation was a success)
# F - Failure (Indicates operation failed and socket should close)
# N - None (None of the above apply)
# D - Data Message (Print as soon as message arrives)

HOST = sys.argv[1] # Server Name
PORT = int(sys.argv[2]) # Port
ADDR = (HOST, PORT)

USER = sys.argv[3] # Username

msg_queue = Queue(maxsize=32) # Used to store command messages for later processing

if USER == '':
    print('Invalid username. Exiting program.')
    exit()

# Create socket:
try:
    print('Creating socket...')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
except:
    print(f'Failed to create socket.')
    sys.exit()

# Logs in to chatroom (or signs up if user already exists):
def login():
    # Connect to server & send username:
    sock.connect(ADDR)
    sock.sendall(bytes(USER, 'utf-8'))
    
    while True:
        response = sock.recv(4096).decode()

        if response[0] == 'I': # Server requests an input
            password = input(response[1:])
            sock.sendall(bytes(password, 'utf-8'))
        elif response[0] == 'S': # Server confirms login was a success
            print(response[1:])
            return 0
        elif response[0] == 'F': # Server confirms login was a failure
            print(response[1:])
            return 1
        else:
            print(response[1:])

def threadFunc():
    while True:
        msg = sock.recv(4096).decode()
        try:
            if (msg[0] == 'D'):
                print('\n' + msg[1:] + '\n')
            else:
                msg_queue.put(msg)
        except:
            return

# Returns oldest command message from queue:
def getMessageFromQueue():
    while msg_queue.empty():
        continue
    return msg_queue.get()

if __name__ == '__main__':
    if login() == 1: # If login fails, exit program
        exit()

    t = threading.Thread(target=threadFunc)
    t.start()
    
    while True:
        # response = sock.recv(4096).decode()
        response = getMessageFromQueue()
        
        # Enter command
        while True:
            command = input('\n' + response[1:] + '\n')

            if command.lower() == 'bm':
                sock.sendall(bytes(command, 'utf-8'))
                # prompt = sock.recv(4096).decode()
                prompt = getMessageFromQueue()
                msg = input(prompt[1:])
                sock.sendall(bytes(msg, 'utf-8'))
                # result = sock.recv(4096).decode()
                result = getMessageFromQueue()
                print(result[1:])
                break
            elif command.lower() == 'pm':
                sock.sendall(bytes(command, 'utf-8'))

                while True:
                    # prompt = sock.recv(4096).decode()
                    prompt = getMessageFromQueue() # Receive list of users

                    if prompt[0] == 'F': # This is true if no other users are online
                        print(prompt[1:])
                        break

                    userToMsg = input(prompt[1:])

                    sock.sendall(bytes(userToMsg, 'utf-8'))
                    # prompt = sock.recv(4096).decode()
                    prompt = getMessageFromQueue()

                    if prompt[0] == 'N':
                        print(prompt[1:])
                        continue
                    elif prompt[0] == 'F':
                        print(prompt[1:])
                        break

                    msg = input(prompt[1:])
                    sock.sendall(bytes(msg, 'utf-8'))
                    # result = sock.recv(4096).decode()
                    result = getMessageFromQueue()
                    print(result[1:])
                    break

                break
            elif command.lower() == 'ex':
                sock.sendall(bytes(command, 'utf-8'))
                t.join(3)
                exit()
            else:
                print('Invalid command. Try again.')
