/**
 * @file
 * @ingroup     app
 *
 * @brief       Mari Gateway application example
 *
 * @author Geovane Fedrecheski <geovane.fedrecheski@inria.fr>
 *
 * @copyright Inria, 2025
 */
#include <nrf.h>
#include <stdio.h>

#include "mr_rng.h"
#include "mr_timer_hf.h"
#include "association.h"

//=========================== defines ==========================================

#define MARI_APP_TIMER_DEV 1

//============================ main ============================================

int main(void) {
    printf("Test Mari Backoff\n");
    mr_timer_hf_init(MARI_APP_TIMER_DEV);

    mr_assoc_init(NULL);

    // test backoff re-schedule execution time (depends on rng)
    size_t   n_runs      = 10;
    uint32_t max_elapsed = 0;
    uint32_t sum_elapsed = 0;
    for (size_t i = 0; i < n_runs; i++) {
        uint32_t start_ts = mr_timer_hf_now(MARI_APP_TIMER_DEV);
        mr_assoc_node_register_collision_backoff();
        uint32_t end_ts  = mr_timer_hf_now(MARI_APP_TIMER_DEV);
        uint32_t elapsed = end_ts - start_ts;
        printf("Collision backoff %d: %d\n", i, elapsed);
        sum_elapsed += elapsed;
        if (elapsed > max_elapsed) {
            max_elapsed = elapsed;
        }
    }

    uint32_t avg_elapsed = sum_elapsed / n_runs;
    printf("Average elapsed us: %d\n", avg_elapsed);
    printf("Max elapsed us: %d\n", max_elapsed);

    // main loop
    while (1) {
        __SEV();
        __WFE();
        __WFE();
    }
}
