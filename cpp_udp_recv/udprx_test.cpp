/** Copyright (C) 2016 - 2020 European Spallation Source ERIC */
#define __STDC_FORMAT_MACROS 1

#include <CLI/CLI.hpp>
#include <cassert>
#include <inttypes.h>
#include <iostream>
#include <common/Socket.h>
#include <common/Timer.h>
#include <stdio.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <chrono>

struct {
  int UDPPort{60000};
  int DataSize{8220};
  int SocketBufferSize{1610612736};

} Settings;


CLI::App app{"UDP receiver with 32 bit sequence number check."};

int main(int argc, char *argv[]) {
  app.add_option("-p, --port", Settings.UDPPort, "UDP receive port");
  app.add_option("-b, --socket_buffer_size", Settings.SocketBufferSize, "socket buffer size (bytes)");
  CLI11_PARSE(app, argc, argv);

  static const int BUFFERSIZE{8220};
  char buffer[BUFFERSIZE];
  uint64_t RxBytesTotal{0};
  uint64_t filenum{0};
  uint64_t RxBytes{0};
  uint64_t RxPackets{0};
  uint16_t SeqNo{0};
  uint16_t SeqNo1{0};
  uint16_t SeqNo2{0};
  uint16_t temp{0};
  const int intervalUs = 1000000;
  const int B1M = 1024*1024;

  Socket::Endpoint local("192.168.90.100", Settings.UDPPort);
  UDPReceiver Receive(local);
  Receive.setBufferSizes(Settings.SocketBufferSize, Settings.SocketBufferSize);
  Receive.printBufferSizes();

  Timer UpdateTimer;
  auto USecs = UpdateTimer.timeus();

  int ReadSize1 = Receive.receive(buffer, BUFFERSIZE);
  SeqNo1 = ntohs(*(uint16_t *)(buffer + 4));
  int ReadSize2 = Receive.receive(buffer, BUFFERSIZE);
  SeqNo2 = ntohs(*(uint16_t *)(buffer + 4));

  assert(ReadSize1 == ReadSize2);


  for (;;) {
    int ReadSize = Receive.receive(buffer, BUFFERSIZE);

    assert(ReadSize > 0);
    assert(ReadSize == Settings.DataSize);

    if (ReadSize > 0) {
      SeqNo = ntohs(*(uint16_t *)(buffer + 4));
      RxBytes += ReadSize;
      //printf("SeqNo: %i %i\n", SeqNo, (0-49999)%49998);
    }


    //printf("seqno %i %i \n", SeqNo, SeqNo2);
    if ((SeqNo2 - SeqNo1) == 0)
        if (!(((SeqNo - SeqNo2) % 2 ) == 1 || ((SeqNo - SeqNo2) % 2 ) == -1))  {
            printf("SeqNo %i %i", SeqNo, SeqNo2);
            //exit(1);

        }


    if ( (SeqNo2 - SeqNo1) % 2 == 1 || (SeqNo2 - SeqNo1) % 2 == -1 )
        //printf("seqno %i %i", SeqNo, SeqNo2);
        //assert(((SeqNo - SeqNo2) % 2 ) == 0) ;
        if(!(((SeqNo - SeqNo2) % 2 ) == 0)) {
            printf("SeqNo %i %i", SeqNo, SeqNo2);
            //exit(1);
        }


    SeqNo1 = SeqNo2;
    SeqNo2 = SeqNo;
   
    auto start = chrono::steady_clock::now();
    if ((RxPackets) % 4000 == 0)
        filenum = filenum % 5;
        std::ofstream out("/dev/shm/temp_" + std::to_string(filenum));

    out.write(buffer+28, ReadSize - 28);


    UpdateTimer.now();
    USecs = UpdateTimer.timeus();

    if ((RxPackets) % 8000 == 7999) {
        out.close();
        filenum += 1;
    }

    auto end = chrono::steady_clock::now();

    if ((RxPackets % 100) == 0)
      USecs = UpdateTimer.timeus();

    if (USecs >= intervalUs) {
      RxBytesTotal += RxBytes;
      printf("Rx rate: %.2f Mbps, rx %" PRIu64 " MB (total: %" PRIu64
             " MB) %" PRIu64 " usecs \n",
             RxBytes * 8.0 / (USecs / 1000000.0) / B1M, RxBytes / B1M, RxBytesTotal / B1M,
             USecs);
      RxBytes = 0;
      UpdateTimer.now();
      USecs = UpdateTimer.timeus();
    }

  if (ReadSize > 0) RxPackets++;

  }
}
