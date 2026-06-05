/**
 * @file
 * @ingroup     app
 *
 * @brief       Metrics collection for the gateway
 *
 * @author Geovane Fedrecheski <geovane.fedrecheski@inria.fr>
 *
 * @copyright Inria, 2025
 */

#include <stdbool.h>

#include "mr_radio.h"
#include "mac.h"
#include "models.h"

#include "metrics.h"

//=========================== types ============================================

typedef struct {
    uint64_t node_id;
    uint32_t tx_count;
    uint32_t rx_count;
} node_metrics_t;

//=========================== variables ========================================

typedef struct {
    node_metrics_t nodes[MARI_N_CELLS_MAX];
} metrics_vars_t;

metrics_vars_t metrics_vars = { 0 };

//=========================== functions ========================================

void metrics_init(void) {
}

void metrics_add_node(uint64_t node_id) {
    for (uint8_t i = 0; i < MARI_N_CELLS_MAX; i++) {
        if (metrics_vars.nodes[i].node_id == 0) {
            metrics_vars.nodes[i].node_id = node_id;
            break;
        }
    }
}

void metrics_clear_node(uint64_t node_id) {
    for (uint8_t i = 0; i < MARI_N_CELLS_MAX; i++) {
        if (metrics_vars.nodes[i].node_id == node_id) {
            metrics_vars.nodes[i].node_id  = 0;
            metrics_vars.nodes[i].tx_count = 0;
            metrics_vars.nodes[i].rx_count = 0;
            break;
        }
    }
}

bool metrics_is_probe(uint8_t *payload, uint32_t payload_len) {
    return payload_len == sizeof(mr_metrics_payload_t) && payload[0] == MARI_PAYLOAD_TYPE_METRICS_PROBE;
}

void metrics_handle_rx_probe(uint64_t node_id, uint8_t *payload) {
    mr_metrics_payload_t *metrics_payload = (mr_metrics_payload_t *)payload;

    metrics_payload->gw_rx_asn  = mr_mac_get_asn();
    metrics_payload->rssi_at_gw = mr_radio_rssi();

    for (uint8_t i = 0; i < MARI_N_CELLS_MAX; i++) {
        if (metrics_vars.nodes[i].node_id == node_id) {
            metrics_payload->gw_rx_count = ++metrics_vars.nodes[i].rx_count;
            break;
        }
    }
}

void metrics_handle_tx_probe(uint64_t node_id, uint8_t *payload) {
    mr_metrics_payload_t *metrics_payload = (mr_metrics_payload_t *)payload;

    metrics_payload->gw_tx_enqueued_asn = mr_mac_get_asn();

    for (uint8_t i = 0; i < MARI_N_CELLS_MAX; i++) {
        if (metrics_vars.nodes[i].node_id == node_id) {
            metrics_payload->gw_tx_count = ++metrics_vars.nodes[i].tx_count;
            break;
        }
    }
}
