response = (
    b"HTTP/1.1 200 OK\r\n"
    b"Server:socket server v0.1\r\n"
    b"Content-Type: text/plain\r\n"
    b"Connection: close\r\n"
    b"\r\n"
    b"<html>\r\n"
    b"<head>\r\n"
    b"    <title>socket server</title>\r\n"
    b"</head>\r\n"
    b"<body>I've got your message</body>\r\n"
    b"</html>\r\n"
)

with open('response.bin', 'wb') as file:
    file.write(response)

print('response.bin created successfully.')