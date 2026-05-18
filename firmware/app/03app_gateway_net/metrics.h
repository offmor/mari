/**
 * @file
 * @brief       Metrics collection for the gateway
 * @details
 *
 * @author Geovane Fedrecheski <geovane.fedrecheski@inria.fr>
 *
 * @copyright Inria, 2025
 */

#ifndef METRICS_H
#define METRICS_H

#include <stdint.h>
#include <stdbool.h>

#include "models.h"

void metrics_init(void);
void metrics_add_node(uint64_t node_id);
void metrics_clear_node(uint64_t node_id);
bool metrics_is_probe(uint8_t *payload, uint32_t payload_len);
void metrics_handle_rx_probe(uint64_t node_id, uint8_t *payload);
void metrics_handle_tx_probe(uint64_t node_id, uint8_t *payload);

#endif  // METRICS_H
