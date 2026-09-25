import os
import socket
from datetime import datetime


class SocketServer:
    def __init__(self):
        # 교수님 코드와 동일하게 버퍼 크기를 1024 bytes로 설정
        self.bufsize = 1024

        # 클라이언트에게 보낼 HTTP 응답 파일
        with open('./response.bin', 'rb') as file:
            self.RESPONSE = file.read()

        # Request 저장 폴더
        self.DIR_PATH = './request'
        self.createDir(self.DIR_PATH)

    def createDir(self, path):
        """
        폴더가 없으면 생성
        """
        try:
            if not os.path.exists(path):
                os.makedirs(path)

        except OSError:
            print("Error: Failed to create the directory.")

    def receiveRequest(self, clnt_sock):
        """
        HTTP Request 전체를 bytes 형식으로 수신한다.

        1. HTTP Header를 먼저 받는다.
        2. Content-Length를 찾는다.
        3. Body를 Content-Length만큼 추가로 받는다.
        """

        request_data = b''

        # -----------------------------------
        # 1. HTTP Header 전체 수신
        # -----------------------------------
        while b'\r\n\r\n' not in request_data:

            data = clnt_sock.recv(self.bufsize)

            if not data:
                break

            request_data += data

        # Header와 Body를 구분할 수 없는 경우
        if b'\r\n\r\n' not in request_data:
            return request_data

        header, body = request_data.split(
            b'\r\n\r\n',
            1
        )

        # -----------------------------------
        # 2. Content-Length 찾기
        # -----------------------------------
        content_length = 0

        header_text = header.decode(
            'iso-8859-1',
            errors='ignore'
        )

        for line in header_text.split('\r\n'):

            if line.lower().startswith('content-length:'):

                content_length = int(
                    line.split(':', 1)[1].strip()
                )

                break

        # -----------------------------------
        # 3. HTTP Body 전체 수신
        # -----------------------------------
        while len(body) < content_length:

            data = clnt_sock.recv(self.bufsize)

            if not data:
                break

            body += data

        # Header + 빈 줄 + Body 복원
        return header + b'\r\n\r\n' + body

    def saveRequest(self, request_data, timestamp):
        """
        실습 1

        HTTP Request 전체를
        년-월-일-시-분-초.bin 파일로 저장
        """

        filename = timestamp + '.bin'

        filepath = os.path.join(
            self.DIR_PATH,
            filename
        )

        with open(filepath, 'wb') as file:
            file.write(request_data)

        print(
            '[실습 1] Request 저장 완료:',
            filepath
        )

    def getBoundary(self, header):
        """
        multipart/form-data에서 boundary를 찾는다.
        """

        header_text = header.decode(
            'iso-8859-1',
            errors='ignore'
        )

        for line in header_text.split('\r\n'):

            if line.lower().startswith('content-type:'):

                if 'boundary=' in line:

                    boundary = line.split(
                        'boundary=',
                        1
                    )[1].strip()

                    # boundary가 " "로 감싸져 있을 경우 제거
                    if (
                        boundary.startswith('"')
                        and boundary.endswith('"')
                    ):
                        boundary = boundary[1:-1]

                    return boundary

        return None

    def saveImage(self, request_data, timestamp):
        """
        실습 2

        multipart/form-data에서
        image 파일 데이터를 찾아 별도 이미지로 저장
        """

        if b'\r\n\r\n' not in request_data:
            print(
                '[실습 2] HTTP Header를 찾을 수 없습니다.'
            )
            return

        # HTTP Header와 Body 분리
        header, body = request_data.split(
            b'\r\n\r\n',
            1
        )

        # multipart boundary 찾기
        boundary = self.getBoundary(header)

        if boundary is None:
            print(
                '[실습 2] multipart boundary가 없습니다.'
            )
            return

        boundary_bytes = (
            '--' + boundary
        ).encode('iso-8859-1')

        # multipart 데이터를 boundary 기준으로 분리
        parts = body.split(boundary_bytes)

        for part in parts:

            # 각 part 앞부분에 붙는 CRLF 제거
            if part.startswith(b'\r\n'):
                part = part[2:]

            # 파일이 아닌 일반 Form Data는 건너뜀
            if b'filename="' not in part:
                continue

            # Header / File Data 구분
            if b'\r\n\r\n' not in part:
                continue

            part_header, file_data = part.split(
                b'\r\n\r\n',
                1
            )

            part_header_text = part_header.decode(
                'iso-8859-1',
                errors='ignore'
            )

            # image 필드인지 확인
            if 'name="image"' not in part_header_text:
                continue

            # -----------------------------------
            # 원래 파일명 찾기
            # -----------------------------------
            original_filename = None

            marker = 'filename="'

            if marker in part_header_text:

                start = (
                    part_header_text.index(marker)
                    + len(marker)
                )

                end = part_header_text.find(
                    '"',
                    start
                )

                original_filename = (
                    part_header_text[start:end]
                )

            if not original_filename:
                continue

            # -----------------------------------
            # multipart에서 파일 뒤 CRLF 제거
            # -----------------------------------
            if file_data.endswith(b'\r\n'):
                file_data = file_data[:-2]

            # 원본 확장자 가져오기
            extension = os.path.splitext(
                original_filename
            )[1]

            if extension == '':
                extension = '.jpg'

            # 날짜시간.jpg 형태로 저장
            image_filename = (
                timestamp + extension
            )

            image_filepath = os.path.join(
                self.DIR_PATH,
                image_filename
            )

            with open(
                image_filepath,
                'wb'
            ) as file:

                file.write(file_data)

            print(
                '[실습 2] Image 저장 완료:',
                image_filepath
            )

            return

        print(
            '[실습 2] 이미지 데이터를 찾지 못했습니다.'
        )

    def run(self, ip, port):
        """
        서버 실행
        """

        # TCP Socket 생성
        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        # 서버 종료 후 포트를 바로 재사용할 수 있도록 설정
        self.sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        # IP와 Port 연결
        self.sock.bind(
            (ip, port)
        )

        # 최대 10개 연결 대기
        self.sock.listen(10)

        print(
            '=========================================='
        )
        print('Start the socket server...')
        print(
            f'Address : http://{ip}:{port}'
        )
        print(
            '"Ctrl+C" for stopping the server!'
        )
        print(
            '==========================================\r\n'
        )

        try:

            while True:

                # -----------------------------------
                # Client 연결 기다리기
                # -----------------------------------
                clnt_sock, req_addr = (
                    self.sock.accept()
                )

                # 최대 5초 대기
                clnt_sock.settimeout(5.0)

                print(
                    '\nRequest message...'
                )

                print(
                    'Client:',
                    req_addr
                )

                try:

                    # -----------------------------------
                    # Request 전체 수신
                    # -----------------------------------
                    response = self.receiveRequest(
                        clnt_sock
                    )

                    print(
                        'Request size:',
                        len(response),
                        'bytes'
                    )

                    # -----------------------------------
                    # 현재 시간
                    # -----------------------------------
                    timestamp = datetime.now().strftime(
                        '%Y-%m-%d-%H-%M-%S'
                    )

                    # -----------------------------------
                    # 실습 1
                    # Request 전체 Binary 저장
                    # -----------------------------------
                    self.saveRequest(
                        response,
                        timestamp
                    )

                    # -----------------------------------
                    # 실습 2
                    # Multipart Image 추출
                    # -----------------------------------
                    self.saveImage(
                        response,
                        timestamp
                    )

                    # -----------------------------------
                    # response.bin 응답 전송
                    # -----------------------------------
                    clnt_sock.sendall(
                        self.RESPONSE
                    )

                except socket.timeout:

                    print(
                        'Socket timeout.'
                    )

                except Exception as e:

                    print(
                        'Error:',
                        e
                    )

                finally:

                    # Client Socket 종료
                    clnt_sock.close()

        except KeyboardInterrupt:

            print(
                '\r\nStop the server...'
            )

        finally:

            # Server Socket 종료
            self.sock.close()


if __name__ == '__main__':

    server = SocketServer()

    # 교수님 자료와 동일한 IP / Port
    server.run(
        '127.0.0.1',
        8000
    )