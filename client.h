#ifndef CLIENT_H_INCLUDED
#define CLIENT_H_INCLUDED

#include <iostream>
#include <winsock.h>

class TcpClient
{
private:
    int portNo;
    char* ipAddress;
    SOCKET mySocket;

public:
    TcpClient(int PortNo, char* IpAddress);
    bool ConnectToHost();
    void SendTcpMessage(char* message);
    void CloseConnection();

};

#endif // CLIENT_H_INCLUDED
