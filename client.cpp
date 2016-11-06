#include "client.h"
    TcpClient::TcpClient(int PortNo = 20000, char* IpAddress = "192.168.0.17")
    {
        portNo = PortNo;
        ipAddress = IpAddress;
    }
    bool TcpClient::ConnectToHost()
    {
        WSADATA wsadata;
        int error = WSAStartup(0x0202, &wsadata);

        if (error){ return false; }

        if (wsadata.wVersion != 0x0202)
        {
        WSACleanup();
        return false;
        }

        SOCKADDR_IN target; //Socket address information

        target.sin_family = AF_INET; // address family Internet
        target.sin_port = htons (portNo); //Port to connect on
        target.sin_addr.s_addr = inet_addr (ipAddress); //Target IP

        mySocket = socket (AF_INET, SOCK_STREAM, IPPROTO_TCP); //Create socket
        if (mySocket == INVALID_SOCKET)
        {
        return false;
        }

        if (connect(mySocket, (SOCKADDR *)&target, sizeof(target)) == SOCKET_ERROR)
        {
        return false;
        }
        return true;
    }
    void TcpClient::SendTcpMessage(char* message)
    {
        send(mySocket,message,strlen(message),0);
    }
    void TcpClient::CloseConnection()
    {
        if (mySocket)
        {
        closesocket(mySocket);
        }

        WSACleanup();
    }
