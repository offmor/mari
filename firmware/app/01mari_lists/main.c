#include <nrf.h>
#include <stdio.h>

#include "scan.h"

//=========================== prototypes ======================================

void test_scan(void);

//============================ main ============================================

int main(void) {
    test_scan();

    // main loop
    while (1) {
        // make sure the event register is cleared
        __SEV();
        __WFE();
        // wait for events, effectively entering System ON sleep mode
        __WFE();
    }
}

// NOTE: this test depends on MARI_MAX_SCAN_LIST_SIZE being 10
void test_scan(void) {
    mr_beacon_packet_header_t beacon = { 0 };

    beacon.src = 1;  // src is the gateway_id
    mr_scan_add(beacon, 1, 37, 1);
    mr_scan_add(beacon, 2, 37, 2);  // update new rssi info wrt gateway_id = 1

    beacon.src = 2;
    mr_scan_add(beacon, 2, 37, 3);
    beacon.src = 3;
    mr_scan_add(beacon, 1, 37, 4);
    beacon.src = 4;
    mr_scan_add(beacon, 1, 37, 5);
    beacon.src = 5;
    mr_scan_add(beacon, 1, 37, 6);
    printf("Selected gateway should be 1: %llu\n", mr_scan_select(1, 7).beacon.src);

    beacon.src = 6;
    mr_scan_add(beacon, 1, 37, 7);
    beacon.src = 7;
    mr_scan_add(beacon, 1, 37, 8);
    beacon.src = 8;
    mr_scan_add(beacon, 1, 37, 9);
    beacon.src = 9;
    mr_scan_add(beacon, 1, 37, 10);
    beacon.src = 10;
    mr_scan_add(beacon, 1, 37, 11);
    beacon.src = 11;
    mr_scan_add(beacon, 1, 37, 12);                                                    // scan list is full, override oldest scan (gateway_id = 1)
    printf("Selected gateway should be 2: %llu\n", mr_scan_select(1, 13).beacon.src);  // and not 1, because 11 overrides 1

    beacon.src = 8;
    mr_scan_add(beacon, 3, 38, 13);
    printf("Selected gateway should be 8: %llu\n", mr_scan_select(1, MARI_SCAN_OLD_US + 5).beacon.src);
}
