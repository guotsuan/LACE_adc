/*
 * main.c
 * Copyright (C) 2021 gq <gq@gqhp>
 *
 * Distributed under terms of the MIT license.
 */

#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>

#include <linux/ip.h> /* for ipv4 header */
#include <linux/udp.h> /* for upd header */

#define ADDR_TO_BIND "192.168.90.100"
#define PORT_TO_BIND 6000

#define MSG_SIZE 256
#define HEADER_SIZE (sizeof(struct iphdr) + sizeof(struct udphdr))

int main(void) {
    int raw_socket;
    struct sockaddr_in sockstr;
    socklen_t socklen;

    int retval = 0; /* the return value (give a look when an error happens)
                     */

    /* no pointer to array!
     * >> It was like "a variable that contains an address -- and in this
     * *    address begins an array of chars"! */
    /* now it is simple an array of chars :-)  */
    char msg[MSG_SIZE];
    ssize_t msglen; /* return value from recv() */

    printf("haha");
    /* do not use IPPROTO_RAW to receive packets */
    if ((raw_socket = socket(AF_INET, SOCK_RAW, IPPROTO_UDP)) == -1) {
      perror("socket");
        return 1; /* here there is no clean up -- retval was not used */
    }
    int disable = 1;
    if (setsockopt(raw_socket, SOL_SOCKET, SO_NO_CHECK, (void*)&disable, sizeof(disable)) < 0) {
        perror("setsockopt failed");
    }

    sockstr.sin_family = AF_INET;
    sockstr.sin_port = htons(PORT_TO_BIND);
    sockstr.sin_addr.s_addr = inet_addr(ADDR_TO_BIND);
    socklen = (socklen_t) sizeof(sockstr);

    /* use socklen instead sizeof()  Why had you defined socklen? :-)  */
    if (bind(raw_socket, (struct sockaddr*) &sockstr, socklen) == -1) {
        perror("bind");
        retval = 1; /* '1' means "Error" */
        goto _go_close_socket;
    }

    memset(msg, 0, MSG_SIZE);
    printf("msg: ", msg);

    if ((msglen = recv(raw_socket, msg, MSG_SIZE, 0)) == -1) {
        perror("recv");
        retval = 1;
        goto _go_close_socket;
    }

    if (msglen <= HEADER_SIZE) /* msg  can't be lesser than header! */
        printf("No msg!\n");
    else {
        msg[msglen - 1] = '\0'; /* we need a null character at the end*/
        printf("Your msg _plus_ headers's size is: %s\n",
               msg + HEADER_SIZE);
    }

_go_close_socket:
    close(raw_socket);

    return retval;
}
