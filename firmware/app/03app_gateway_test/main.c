/**
 * @file
 * @ingroup     app
 *
 * @brief       Mari Gateway application (radio side)
 *
 * @author Geovane Fedrecheski <geovane.fedrecheski@inria.fr>
 *
 * @copyright Inria, 2025
 */
#include <nrf.h>
#include <stdio.h>

#include "mr_device.h"
#include "mr_radio.h"
#include "mr_timer_hf.h"
#include "scheduler.h"
#include "mari.h"
#include "packet.h"

//=========================== defines ==========================================

#define MARI_APP_TIMER_DEV 1

#define DATA_LEN 4

typedef struct {
    bool dummy;
} gateway_vars_t;

typedef struct {
    uint32_t n_downlink;  ///< Number of packets sent to nodes (as unicast)
    uint32_t n_uplink;    ///< Number of packets received from nodes
} stats_vars_t;

//=========================== variables ========================================

gateway_vars_t gateway_vars = { 0 };

stats_vars_t stats_vars = { 0 };

uint8_t packet[MARI_PACKET_MAX_SIZE] = { 0 };
uint8_t payload[]                    = { 0xFA, 0xFA, 0xFA, 0xFA, 0xFA };
uint8_t payload_len                  = 5;

extern schedule_t schedule_minuscule, schedule_tiny, schedule_huge;

schedule_t *schedule_app = &schedule_huge;

//=========================== prototypes =======================================

void mari_event_callback(mr_event_t event, mr_event_data_t event_data);
void tx_to_all_connected(void);
void stats_register(uint8_t type);
void _debug_print_stats(void);

//=========================== main =============================================

int main(void) {
    printf("Hello Mari Gateway Net Core %016llX\n", mr_device_id());
    mr_timer_hf_init(MARI_APP_TIMER_DEV);

    mr_timer_hf_set_periodic_us(MARI_APP_TIMER_DEV, 0, 1000 * 750, &tx_to_all_connected);

    mr_timer_hf_set_periodic_us(MARI_APP_TIMER_DEV, 1, 1000 * 1005, &_debug_print_stats);

    mari_init(MARI_GATEWAY, MARI_NET_ID_DEFAULT, schedule_app, &mari_event_callback);

    mr_timer_hf_set_periodic_us(MARI_APP_TIMER_DEV, 2, mr_scheduler_get_duration_us(), &mari_event_loop);

    while (1) {
        __SEV();
        __WFE();
        __WFE();
    }
}

//=========================== callbacks ========================================

void mari_event_callback(mr_event_t event, mr_event_data_t event_data) {
    (void)event_data;
    uint32_t now_ts_s = mr_timer_hf_now(MARI_APP_TIMER_DEV) / 1000 / 1000;
    switch (event) {
        case MARI_NEW_PACKET:
        {
            stats_register('U');
            break;
        }
        case MARI_NODE_JOINED:
            printf("%d New node joined: %016llX  (%d nodes connected)\n", now_ts_s, event_data.data.node_info.node_id, mari_gateway_count_nodes());
            break;
        case MARI_NODE_LEFT:
            printf("%d Node left: %016llX, reason: %u  (%d nodes connected)\n", now_ts_s, event_data.data.node_info.node_id, event_data.tag, mari_gateway_count_nodes());
            break;
        case MARI_ERROR:
            printf("Error, reason: %u\n", event_data.tag);
            break;
        default:
            break;
    }
}

//=========================== private ========================================

void tx_to_all_connected(void) {
    uint64_t nodes[MARI_MAX_NODES] = { 0 };
    uint8_t  nodes_len             = mari_gateway_get_nodes(nodes);
    for (int i = 0; i < nodes_len; i++) {
        // printf("Enqueing TX to node %d: %016llX\n", i, nodes[i]);
        payload[0]         = i;
        uint8_t packet_len = mr_build_packet_data(packet, nodes[i], payload, payload_len);
        mari_tx(packet, packet_len);
        stats_register('D');
    }
}

void stats_register(uint8_t type) {
    if (type == 'D') {
        stats_vars.n_downlink++;
    } else if (type == 'U') {
        stats_vars.n_uplink++;
    }
}

void _debug_print_stats(void) {
    uint32_t now_ts_ms = mr_timer_hf_now(MARI_APP_TIMER_DEV) / 1000;
    uint32_t now_ts_s  = now_ts_ms / 1000;
    // calculate success rate
    float rate = (float)stats_vars.n_uplink / (float)stats_vars.n_downlink * 100.0;
    printf("ts = %d.%d Success = %.2f%%: %u downlink packets, %u uplink packets\n", now_ts_s, now_ts_ms, rate, stats_vars.n_downlink, stats_vars.n_uplink);
}
