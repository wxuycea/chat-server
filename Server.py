# 안녕현수
# Server.py
import socket
import threading
import re

# 접속 배너
welcome_message = """
 /\＿/\ 
(„• - •„)
┏∪∪━━━━━━━━━━━━━━━┓
┃  채팅 프로그램에 접속하였습니다  ┃
┗━━━━━━━━━━━━━━━━━┛
"""

# 이름 유효성 검사를 위한 정규표현식
name_pattern = re.compile(r'^[가-힣][가-힣\s]{0,9}$')

def handle_client(client_socket, clients, names, welcome_message, addr):
    while True:   #-- 올바른 이름 입력까지 반복
        client_name = client_socket.recv(1024).decode()
        # 중복된 이름과 규칙 어긴 이름 필터링
        if client_name in names:
            client_socket.send("※ 이미 있는 이름입니다.".encode())
        elif not name_pattern.match(client_name):
            client_socket.send("※ 한글로 1~10글자 입력해주세요.".encode())
        else:
            names.append(client_name)
            print(f"{client_name} 님이 접속하였습니다. {addr}")
            client_socket.send(welcome_message.encode())
            #client_socket.send()
            break # 올바른 이름 입력 시 종료

    while True:
        try:    #-- 채팅을 계속 받는 곳
            data = client_socket.recv(1024)
            if not data:
                break
            message = data.decode()
            
            # 클라이언트가 퇴장하려는 경우
            if message.lower() == "exit":
                client_index = clients.index(client_socket)
                client_name = names[client_index]

                # 다른 클라이언트에게 퇴장 정보 브로드캐스트
                print(f"{client_name} 님이 퇴장하였습니다.")
                leave_message = f"{client_name} 님이 퇴장하였습니다."
                for client in clients:
                    if client != client_socket:
                        client.send(leave_message.encode())

                # 클라이언트와의 연결이 끊겼을 때 처리
                client_socket.close()
                client_index = clients.index(client_socket)
                clients.remove(client_socket)
                names.pop(client_index)
            else:
                # 클라이언트 메시지를 서버에 출력
                print(f"[{client_name}] {message}")
                # 브로드캐스트: 모든 클라이언트에게 메시지를 전송
                for client in clients:
                    client.send(f"[{client_name}] {message}".encode())

        except ConnectionError:
            break
        except Exception as e:
            print(f"메시지 수신 중 오류 발생: {e}")
            break

    # 클라이언트와의 연결이 끊겼을 때 처리
    client_socket.close()
    client_index = clients.index(client_socket)
    clients.remove(client_socket)
    names.pop(client_index)

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1", 8732))
    server_socket.listen(5)
    print("채팅 서버가 열렸습니다.\n")

    clients = []
    names = []

    while True:
        client_socket, addr = server_socket.accept()

        clients.append(client_socket)

        # 각 클라이언트를 위한 스레드 시작
        client_handler = threading.Thread(target=handle_client, args=(client_socket, clients, names, welcome_message, addr))
        client_handler.start()

if __name__ == "__main__":
    main()
