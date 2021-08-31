/** Copyright (C) 2016 - 2020 European Spallation Source ERIC */
#define __STDC_FORMAT_MACROS 1

#include <CLI/CLI.hpp>
#include <cassert>
#include <inttypes.h>
#include <iostream>
#include <common/Socket.h>
#include <common/Timer.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <chrono>
#include <thread>

#define UDP_RAW


using namespace std;
struct {
  int UDPPort{60000};
  int DataSize{8220};
  int SocketBufferSize{1073741824};

} Settings;


CLI::App app{"UDP receiver with 32 bit sequence number check."};

void output(std::ofstream &ff, char *buffer, uint64_t &pos, int lsize) 
{
    ff.seekp(pos);
    ff.write(buffer, lsize);
    pos += lsize;
}

int main(int argc, char *argv[]) {
  app.add_option("-p, --port", Settings.UDPPort, "UDP receive port");
  app.add_option("-b, --socket_buffer_size", Settings.SocketBufferSize, "socket buffer size (bytes)");
  CLI11_PARSE(app, argc, argv);

  static const int BUFFERSIZE{8200};
  char buffer[BUFFERSIZE];
  uint64_t RxBytesTotal{0};
  uint64_t filenum{0};
  uint64_t RxBytes{0};
  uint64_t RxPackets{0};
  uint32_t SeqNo{0};
  uint32_t SeqNo1{0};
  uint32_t SeqNo2{0};
  uint16_t temp{0};
  uint64_t write_cnt{0};
  uint64_t file_p{0};
  uint64_t disc_cnt{0};
  uint64_t lost_p{0};
  const int intervalUs = 1000000;
  const int block_size = 4096;
  const int B1M = 1024*1024;
  const int load_size = 8200;
  const int packet_size = 8200;
  const int cycle = 65535;
  const int id_offset = load_size - 4;
  std::ofstream out;
  int status_before;
  int status_now;
  int rxbuf;
  int txbuf;

  bool skippable = false; 
  // TOFIX: skip the whole block if a packet is lost
  bool bad_block = true;
  bool loop_files = true;

  Socket::Endpoint local("192.168.90.100", Settings.UDPPort);

  Timer UpdateTimer;
  auto USecs = UpdateTimer.timeus();

  //auto start = chrono::steady_clock::now();
  UDPReceiver Receive(local);
  Receive.setBufferSizes(Settings.SocketBufferSize, Settings.SocketBufferSize);
  Receive.printBufferSizes();

start_over:
  RxBytesTotal = 0;
  RxPackets = 0;

  for (int i;i<block_size;i++) {
      int ReadSize1 = Receive.receive(buffer, BUFFERSIZE);
  }

  int ReadSize1 = Receive.receive(buffer, BUFFERSIZE);
  int ReadSize2 = Receive.receive(buffer, BUFFERSIZE);
  //SeqNo1 = ntohs(*(uint16_t *)(buffer + 4));
  //SeqNo1 = ntohs(*(uint32_t *)(buffer + 8226));
  //SeqNo2 = ntohs(*(uint16_t *)(buffer + 4));
  //SeqNo2 = ntohs(*(uint32_t *)(buffer + 8226));
  SeqNo1 = ntohl(*(uint32_t *)(buffer + id_offset));
  //SeqNo2 = ntohs(*(uint16_t *)(buffer + 4));
  SeqNo2 = ntohl(*(uint32_t *)(buffer + id_offset));

  printf("S1, S2, %i, %i", SeqNo1, SeqNo2);
  //assert(ReadSize1 == ReadSize2);

  for (;;) {
    bad_block = false;
    int ReadSize = Receive.receive(buffer, BUFFERSIZE);

    assert(ReadSize > 0);
    assert(ReadSize == Settings.DataSize);

    if (ReadSize > 0) {
      //SeqNo = ntohs(*(uint16_t *)(buffer + 4));
      //SeqNo = ntohs(*(uint32_t *)(buffer + 8224));
      SeqNo = ntohl(*(uint32_t *)(buffer + id_offset));
      RxBytes += ReadSize;
    }


    //printf("seqno %i %i \n", SeqNo, SeqNo2);
    //
    status_before = SeqNo2 - SeqNo1;
    status_now = SeqNo - SeqNo2;
    switch(status_now) {
        case 1: 
        case 4:
            break;
        case -cycle:
            printf("cycle sequence is not continuous: SeqNo %i %i %i, start over \n", SeqNo1, SeqNo2, SeqNo);
            break;
        default:
            printf("2 sequence is not continuous: SeqNo %i %i %i, start over \n", SeqNo1, SeqNo2, SeqNo);
            auto end = chrono::steady_clock::now();
            printf("time %f \n",  end-start);
            //disc_cnt ++;
            //if (RxPackets < 500)
                //goto start_over;
            lost_p ++;
            bad_block = true;
                //exit(1);
    }


    SeqNo1 = SeqNo2;
    SeqNo2 = SeqNo;
   
    //auto start = chrono::steady_clock::now();
    //if ((RxPackets) % block_size == 0) {
        //if (loop_files)
            //filenum = filenum % 5;
        //write_cnt = 0;
        //file_p = 0;
        //out.open("/dev/shm/temp_" + std::to_string(filenum), 
                //std::ofstream::binary|std::ofstream::trunc);
    //}


    //if (out.is_open()) {
        //out.seekp(file_p);
        //out.write(buffer, load_size);
        ////out.flush();  is no obviously helpful
        //file_p += load_size;
        //write_cnt++;
    //}


    //if (write_cnt == block_size && out.is_open()) {
        //out.close();
        //if (!(skippable && bad_block))
            //filenum += 1;
    //}

    //auto end = chrono::steady_clock::now();

    //printf("packs %i, time %f \n", RxPackets, end-start);
    if ((RxPackets % 100) == 0)
      USecs = UpdateTimer.timeus();

    if (USecs >= intervalUs) {
      RxBytesTotal += RxBytes;
      //printf("Rx rate: %.2f Mbps, rx %" PRIu64 " MB (total: %" PRIu64
             //" MB) %" PRIu64 " usecs, lost %i ps of total %i \n",
             //RxBytes * 8.0 / (USecs / 1000000.0) / B1M, RxBytes / B1M, RxBytesTotal / B1M,
             //USecs, lost_p, RxPackets);
      RxBytes = 0;
      UpdateTimer.now();
      USecs = UpdateTimer.timeus();
    }

  if (ReadSize > 0) RxPackets++;

  if (disc_cnt > 10) {
      printf("You have a broken heart, check your code again! \n");
      exit(1);
  }

  }
}
