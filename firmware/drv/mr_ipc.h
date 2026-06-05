#ifndef __MR_IPC_H
#define __MR_IPC_H

/**
 * @brief       Read the RNG peripheral
 *
 * @{
 * @file
 * @author Alexandre Abadie <alexandre.abadie@inria.fr>
 * @author Geovane Fedrecheski <geovane.fedrecheski@inria.fr>
 * @copyright Inria, 2025-now
 * @}
 */

#include <stdint.h>
#include <stdbool.h>

//=========================== defines ==========================================

#define IPC_IRQ_PRIORITY (1)

typedef enum {
    MR_IPC_REQ_NONE,      ///< Sorry, but nothing
    MR_IPC_RNG_INIT_REQ,  ///< Request to initialize the RNG peripheral
    MR_IPC_RNG_READ_REQ,  ///< Request to read the RNG peripheral
} ipc_req_t;

typedef enum {
    MR_IPC_CHAN_REQ        = 0,  ///< Channel used for request events
    MR_IPC_CHAN_MARI_EVENT = 1,  ///< Channel used for mari events
} ipc_channels_t;

typedef struct {
    uint8_t value;  ///< Byte containing the random value read
} ipc_rng_data_t;

typedef struct __attribute__((packed)) {
    bool           net_ready;  ///< Network core is ready
    bool           net_ack;    ///< Network core acked the latest request
    ipc_req_t      req;        ///< IPC network request
    ipc_rng_data_t rng;        ///< Rng share data
} ipc_shared_data_t;

//=========================== prototypes =======================================

#endif  // __MR_IPC_H
