# Server.py
import socket
import threading
import re

# 접속 배너
welcome_message = """
 /\＿/\ 
(„• - •„)
┏∪∪━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  채팅 프로그램에 접속하였습니다  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""

help_message = """
명령어 설명(/help)

/list : 채팅방에 접속한 사용자들을 출력합니다.
/newchat [채팅방이름] : 채팅방을 생성합니다. 생성 후 그 채팅방의 관리자가 됩니다.
/delchat [채팅방이름] : 채팅방을 삭제합니다. 관리자만이 삭제 가능합니다.
/chatlist : 현재 존재하는 채팅방들을 출력합니다.
/chat [채팅방이름] : 해당 채팅방에 입장합니다.
/mychat : 현재 접속해있는 채팅방 이름을 출력합니다.
/w [상대방이름] [메시지] : 특정 사용자에게만 메시지를 보냅니다.(귓속말)
/help : 명령어에 대한 설명을 출력합니다.
"""

clients = []
names = []
chat_rooms = {"로비": []}  # "로비" 채팅방을 서버 시작 시 생성
chat_room_admins = {}

# 이름 유효성 검사를 위한 정규표현식
name_pattern = re.compile(r'^[가-힣][가-힣\s]{0,9}$')

def handle_list_command(client_socket, chat_rooms, client_info):
    current_chat_room = client_info.get("current_chat_room")
    if current_chat_room and current_chat_room in chat_rooms:
        chat_room_clients = chat_rooms[current_chat_room]
        client_list = "\n".join([f"{i + 1}. {names[clients.index(client)]}" for i, client in enumerate(chat_room_clients)])
        client_socket.send(f"\n[{current_chat_room} 채팅방 접속자]\n{client_list}\n".encode())
    else:
        client_socket.send("현재 어떤 채팅방에도 속해있지 않습니다.\n".encode())


def handle_newchat_command(client_socket, chat_rooms, chat_room_admins, client_name, client_info, message):
    parts = message.split(maxsplit=1)
    if len(parts) < 2:
        client_socket.send("명령어 뒤에 채팅방 이름을 함께 입력해주세요.".encode())
        return

    chat_room_name = parts[1].strip()
    if chat_room_name:
        if chat_room_name in chat_rooms:
            client_socket.send(f"'{chat_room_name}' 채팅방은 이미 존재합니다.".encode())
        else:
            # 이전 채팅방에서 나가기
            previous_chat_room = client_info.get("current_chat_room")
            if previous_chat_room:
                chat_rooms[previous_chat_room].remove(client_socket)

            # 새 채팅방 생성 및 입장
            chat_rooms[chat_room_name] = []
            chat_room_admins[chat_room_name] = client_name  # 관리자 설정
            client_socket.send(f"'{chat_room_name}' 채팅방이 생성되었습니다.".encode())
            print(f"'{chat_room_name}' 채팅방이 생성되었습니다.")
            client_info["current_chat_room"] = chat_room_name
            chat_rooms[chat_room_name].append(client_socket)

            # "로비"에 채팅방 생성 알림 보내기
            notification_message = f"'{chat_room_name}' 채팅방이 생성되었습니다."
            for client in chat_rooms["로비"]:
                client.send(notification_message.encode())

            client_socket.send(f"'{chat_room_name}' 채팅방에 입장했습니다.".encode())
    else:
        client_socket.send("명령어 뒤에 채팅방 이름을 함께 입력해주세요.".encode())

def handle_chatlist_command(client_socket, chat_rooms):
    chat_room_list = "\n".join([f"{i + 1}. {chat_room}" for i, chat_room in enumerate(chat_rooms.keys())])
    client_socket.send(f"\n[채팅방 목록]\n{chat_room_list}\n".encode())

def handle_chat_command(client_socket, message, chat_rooms, client_info, client_name):
    parts = message.split(maxsplit=1)
    if len(parts) < 2:
        client_socket.send("명령어 뒤에 채팅방 이름을 함께 입력해주세요.".encode())
        return

    chat_room_name = parts[1].strip()
    if chat_room_name in chat_rooms:
        # 이전 채팅방에서 나가기
        previous_chat_room = client_info.get("current_chat_room")
        if previous_chat_room:
            chat_rooms[previous_chat_room].remove(client_socket)

        # 새 채팅방에 입장
        client_info["current_chat_room"] = chat_room_name
        chat_rooms[chat_room_name].append(client_socket)
        client_socket.send(f"'{chat_room_name}' 채팅방에 입장했습니다.".encode())
    else:
        client_socket.send("존재하지 않는 채팅방입니다.".encode())

def handle_delchat_command(client_socket, chat_rooms, client_name, message):
    # 메시지에서 명령어와 채팅방 이름을 분리합니다.
    parts = message.split(maxsplit=1)
    
    if len(parts) < 2:
        # 메시지가 명령어와 채팅방 이름 두 부분으로 나뉘지 않은 경우
        client_socket.send("명령어 뒤에 채팅방 이름을 함께 입력해주세요.".encode())
    else:
        command, chat_room_name = parts
        chat_room_name = chat_room_name.strip()  # 채팅방 이름 앞뒤 공백 제거
        
        if client_name in chat_room_admins and chat_room_admins[client_name] in chat_rooms:
            if chat_room_name in chat_rooms:
                # 채팅방 삭제
                del chat_rooms[chat_room_name]
                del chat_room_admins[client_name]
                client_socket.send(f"'{chat_room_name}' 채팅방이 삭제되었습니다.".encode())
            else:
                client_socket.send("존재하지 않는 채팅방입니다.".encode())
        else:
            client_socket.send("관리자만 채팅방을 삭제할 수 있습니다.".encode())

def handle_mychat_command(client_socket, client_info):
    current_chat_room = client_info.get("current_chat_room")
    if current_chat_room:
        client_socket.send(f"현재 접속 중인 채팅방: {current_chat_room}\n".encode())
    else:
        client_socket.send("현재 어떤 채팅방에도 입장하지 않았습니다.\n".encode())


def handle_w_command(client_socket, message, names):
    parts = message.split(maxsplit=2)   # 메시지 분리
    if len(parts) == 3:
        target_name = parts[1]  # 귓속말 대상
        private_message = parts[2]  # 귓속말 메시지

        if target_name in names:
            target_index = names.index(target_name)
            target_socket = clients[target_index]
            sender_name = names[clients.index(client_socket)]

            client_socket.send(f"[귓속말] {sender_name} -> {target_name}: {private_message}".encode())
            target_socket.send(f"[귓속말] {sender_name} -> {target_name}: {private_message}".encode())
        else:
            client_socket.send("귓속말 대상 클라이언트가 존재하지 않습니다.".encode())
    else:
        client_socket.send("올바른 귓속말 형식이 아닙니다. /w [대상 클라이언트 이름] [메시지] 형식으로 입력하세요.".encode())


def handle_client(client_socket, addr):
    client_info = {"current_chat_room": "로비"}  # 클라이언트 정보 딕셔너리 초기화
    client_name = None
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
            client_socket.send("로비에 입장하였습니다.\n".encode())
            client_socket.send("명령어 사용에 대해서는 /help 를 이용해주세요.\n".encode())
            break # 올바른 이름 입력 시 종료

    while True:
        try:    # 채팅을 계속 받는 곳
            data = client_socket.recv(1024)
            if not data:
                break
            message = data.decode()
            
            # 클라이언트가 퇴장하려는 경우
            if message.lower() == "exit":
                client_index = clients.index(client_socket)
                client_name = names[client_index]

                # 현재 채팅방에서 클라이언트 제거
                current_chat_room = client_info.get("current_chat_room")
                if current_chat_room and client_socket in chat_rooms[current_chat_room]:
                    chat_rooms[current_chat_room].remove(client_socket)

                # 다른 클라이언트에게 퇴장 정보 브로드캐스트
                print(f"{client_name} 님이 퇴장하였습니다.")
                leave_message = f"{client_name} 님이 퇴장하였습니다."
                for client in clients:
                    if client != client_socket:
                        client.send(leave_message.encode())
                
            elif message.startswith("/"):
                if message.startswith("/list"):  # 현재 채팅방 접속자 목록
                    handle_list_command(client_socket, chat_rooms, client_info)
                elif message.startswith("/newchat"):    # 채팅방 생성
                    handle_newchat_command(client_socket, chat_rooms, chat_room_admins, client_name, client_info, message)
                elif message.strip() == "/chatlist":    # 생성된 채팅방 목록
                    handle_chatlist_command(client_socket, chat_rooms)
                elif message.startswith("/chat"):   # 채팅방 접속
                    handle_chat_command(client_socket, message, chat_rooms, client_info, client_name)
                elif message.strip() == "/delchat": # 채팅방 삭제
                    handle_delchat_command(client_socket, chat_rooms, client_name, message)
                elif message.strip() == "/help":    # 명령어 출력
                    client_socket.send(help_message.encode())
                elif message.strip() == "/w":   # 귓속말
                    handle_w_command(client_socket, message, names)
                elif message.strip() == "/mychat":  # 현재 접속 중인 채팅방 출력
                    handle_mychat_command(client_socket, client_info)
                    
            else:
                # 메시지를 현재 채팅방에 속한 클라이언트들에게만 전송
                current_chat_room = client_info.get("current_chat_room")
                if current_chat_room:
                    for client in chat_rooms.get(current_chat_room, []):
                        if client != client_socket:
                            client.send(f"[{client_name}] {message}".encode())

        except ConnectionError:
            break
        except Exception as e:
            print(f"메시지 수신 중 오류 발생: {e}")
            continue

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

    # "robby" 채팅방 생성
    chat_rooms["로비"] = []

    while True:
        client_socket, addr = server_socket.accept()

        clients.append(client_socket)

        # 클라이언트를 "로비" 채팅방에 자동으로 입장
        chat_rooms["로비"].append(client_socket)

        # 각 클라이언트를 위한 스레드 시작
        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_handler.start()

if __name__ == "__main__":
    main()