import socket
import time


class PyBridge:

    def __init__(self, input_score_list:list, verbosity:bool=False) -> None:
        self.event_loop_enabled = True
        self.sleep_timer = 1
        self.score_list = input_score_list
        self.verbosity = verbosity

    def cond_print(self, msg:str) -> None:
        if self.verbosity: print(msg)

    def set_listener(self,
                    host:str = 'localhost',
                    port:int = 1337,
                    timeout:int = 5,
                    disable_timeout:bool = False
                    ) -> None:

        self.sock = socket.socket()
        self.sock.bind((host, port))
        self.sock.listen(1)
        if disable_timeout: timeout = None 
        self.sock.settimeout(timeout)

    def dynamic_sleep(self, sleep:int) -> None:
        self.sleep_timer = sleep

    def start_listening(self) -> None:
        self.clientsocket = None
        self.clientsocket, self.address = self.sock.accept()
        self.cond_print(f"Connection form {self.address} has been established!")
        self.connection = True

    def start_streaming(self) -> None:
        try:
            client_waiting = True
            while self.event_loop_enabled:
                if client_waiting:
                    if self.score_list != []:
                        data = self.score_list.pop(0)
                        self.cond_print(f'Sending: {data}')
                        self.clientsocket.send(bytes(str(data), 'utf8'))
                        client_waiting = False
                    else: time.sleep(self.sleep_timer) # Reduces cpu usage
                else:
                    self.cond_print('Waiting for respone')
                    self.clientsocket.recv(1)
                    self.cond_print('Respond recieved\nSending new more data, if there is any')
                    client_waiting = True

        except KeyboardInterrupt:
            print('\nKeyboard interrupt recieved, closing connection')
        finally:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()


def example() -> None:
    score_list = [x for x in range(0,101)]
    default = PyBridge(score_list)
    default.set_listener(disable_timeout=True)
    default.start_listening()
    default.start_streaming()