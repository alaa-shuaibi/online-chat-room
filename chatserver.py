import socket
import threading
import sys
import json

# Server Data Encoding:
# I - Input (Indicates a request for input)
# S - Success (Indicates operation was a success)
# F - Failure (Indicates operation failed and socket should close)
# N - None (None of the above apply)

HOST = socket.gethostbyname(socket.gethostname())
PORT = int(sys.argv[1]) # Port
ADDR = (HOST, PORT)

maxThreadNumber = 10
threads = []
active_clients = {} # Key is username, value is user's socket

# Load current users:
with open('users.json', 'r') as f:
    users = json.load(f)

# Thread function for connection with a client:
def connectionFunc(clientSock):
    with clientSock:
        username = clientSock.recv(4096).decode()

        if username in users: # username exists, request password
            numAttempts = 2
            while True:
                clientSock.sendall(b'IEnter your password: ')
                password = clientSock.recv(4096).decode()
                numAttempts -= 1

                if users[username] == password: # password is correct
                    clientSock.sendall(b'SSuccessfully logged in!')
                    break
                elif numAttempts > 0: # password is incorrect
                    clientSock.sendall(b'NIncorrect. 1 attempt remaining.')
                else: # password is incorrect and number of login attempts ran out
                    clientSock.sendall(b'FIncorrect. 0 attempts remaining. Closing connection.')
                    clientSock.close()
                    return
        else: # username does not exist, request a new password
            numAttempts = 2
            while True:
                clientSock.sendall(b'ICreate a new password: ')
                new_password = clientSock.recv(4096).decode()
                
                if new_password != '':
                    users[username] = new_password
                    with open('users.json', 'w') as f:
                        json.dump(users, f)
                    clientSock.sendall(b'SSuccessfully created a new password!')
                    break
                elif numAttempts > 0:
                    clientSock.sendall(b'NInvalid password. 1 attempt remaining.')
                else:
                    clientSock.sendall(b'FInvalid password. 0 attempts remaining. Closing connection.')
                    clientSock.close()
                    return

        active_clients[username] = clientSock # Once logged in, adds client to list of active clients.
        print(username + ' logged in.')

        while True:
            clientSock.sendall(b'IEnter one of the following commands to continue:\n' + 
                                b'BM - Broadcast Messaging\n' +
                                b'PM - Private Messaging\n'
                                b'EX - Exit\n')
            command = clientSock.recv(4096).decode().lower()
            
            if command == 'bm':
                clientSock.sendall(b'IEnter message to send: ')
                msg = 'D' + username + ': ' + clientSock.recv(4096).decode()

                for c in active_clients:
                    if c == username:
                        continue
                    try:
                        active_clients[c].sendall(bytes(msg, 'utf-8'))
                    except:
                        continue # If msg failed to send to user, continue anwyway
                
                clientSock.sendall(b'SMessage was sent to all active users.')
            elif command == 'pm':
                list_of_users = 'I\nUsers currently online:\n'
                for c in active_clients:
                    if c == username:
                        continue
                    list_of_users += '- ' + c + '\n'
                list_of_users += '\nSelect a user to message: '

                msgIsCancelled = False
                while True:
                    if len(active_clients) <= 1:
                        clientSock.sendall(b'F0 users online. Cancelling operation...')
                        msgIsCancelled = True
                        break

                    clientSock.sendall(bytes(list_of_users, 'utf-8'))
                    userToMsg = clientSock.recv(4096).decode()
                    
                    if userToMsg.lower() == 'ex':
                        clientSock.sendall(b'FCancelled message.\n')
                        msgIsCancelled = True
                        break
                    
                    if userToMsg in active_clients:
                        clientSock.sendall(b'IEnter the message to send: ')
                        break
                    
                    clientSock.sendall(b'NUser not online. Enter \'EX\' to cancel operation or try again.\n')
                
                if msgIsCancelled:
                    continue

                msg = 'D' + username + ': ' + clientSock.recv(4096).decode()

                try:
                    active_clients[userToMsg].sendall(bytes(msg, 'utf-8'))
                    clientSock.sendall(b'SSuccessfully sent the message!')
                except:
                    clientSock.sendall(b'FFailed to send message.')

            elif command == 'ex':
                break
            else:
                print('Invalid Command.')
    
    clientSock.close()
    del active_clients[username] # Removes client from list of active clients.
    print(username + ' logged out.')

if __name__ == '__main__':
    # print(HOST)

    # Create & bind socket:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.bind(ADDR)
        sock.listen()
    except:
        print(f'Failed to set up socket.')
        sys.exit()

    # Wait for connections:
    while True:
        clientSock, clientADDR = sock.accept()

        if len(threads) >= maxThreadNumber:
            clientSock.sendall(b'FServer capacity is full. Please try again later.')
            clientSock.close()
            continue

        t = threading.Thread(target=connectionFunc, args=(clientSock))
        threads.append(t)
        t.start()
