# Client.py
import socket
import threading

def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024)
            if not message:
                break
            print(message.decode())
        except ConnectionError:
            print("서버와의 연결이 끊어졌습니다.")
            break
        except Exception as e:
            print(f"예외 발생: {e}")
            break

def main():
    # step0. connection
    server_ip = "127.0.0.1"  # 서버의 IP 주소
    server_port = 9113  # 서버의 포트 번호
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4, TCP
    client_socket.connect((server_ip, server_port))

    # step1. get username
    # name = input("\n이름을 입력하세요: ")
    # client_socket.send(name.encode())

    # set thread method
    message_receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    message_receive_thread.start() # launch thread

    try:
        while True:
            # get message text
            message = input()

            # # 종료 옵션
            # if message == "exit":
            #     client_socket.send(message.encode())
            #     break

            # send message
            print(message)
            client_socket.send(message.encode())
    except KeyboardInterrupt:   #-- 검토
        pass  # Ctrl+C로 인한 종료
    finally:
        client_socket.close()  # 종료 시 소켓을 닫음


    client_socket.close()

if __name__ == "__main__":
    main()
