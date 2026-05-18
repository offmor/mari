/**
 * @file
 * @ingroup bsp_rng
 *
 * @brief  nRF52840-specific definition of the "rng" bsp module.
 *
 * @author Alexandre Abadie <alexandre.abadie@inria.fr>
 *
 * @copyright Inria, 2023
 */
#include <nrf.h>
#include <stdint.h>

#include "mr_rng.h"

#if defined(NRF5340_XXAA) && defined(NRF_NETWORK)
#define NRF_RNG NRF_RNG_NS
#endif

//=========================== public ===========================================

void mr_rng_init(void) {

    // Enable bias correction, slower but uniform
    NRF_RNG->CONFIG = (RNG_CONFIG_DERCEN_Enabled << RNG_CONFIG_DERCEN_Pos);

    // Enable value ready event
    NRF_RNG->INTENSET = (RNG_INTENSET_VALRDY_Enabled << RNG_INTENSET_VALRDY_Pos);

    // Automatically stop when value is ready
    NRF_RNG->SHORTS = (RNG_SHORTS_VALRDY_STOP_Enabled << RNG_SHORTS_VALRDY_STOP_Pos);
}

void mr_rng_read_u8(uint8_t *value) {
    NRF_RNG->TASKS_START = 1;
    while (NRF_RNG->EVENTS_VALRDY == 0) {};
    *value                 = (uint8_t)NRF_RNG->VALUE;
    NRF_RNG->EVENTS_VALRDY = 0;
}

void mr_rng_read_u16(uint16_t *value) {
    // read 2 bytes from the RNG
    uint8_t raw_low, raw_high;
    mr_rng_read_u8(&raw_low);
    mr_rng_read_u8(&raw_high);
    // combine the two bytes into a 16-bit number (we need 16 bits because MARI_BACKOFF_N_MAX > 8)
    *value = ((uint16_t)raw_high << 8) | (uint16_t)raw_low;
}

void mr_rng_read_range(uint8_t *value, uint8_t min, uint8_t max) {
    do {
        mr_rng_read_u8(value);
    } while (!(*value >= min && *value < max));
}

void mr_rng_read_u8_fast(uint8_t *value) {
    // Temporarily disable bias correction for faster reads
    uint32_t original_config = NRF_RNG->CONFIG;
    NRF_RNG->CONFIG          = 0;  // Disable bias correction

    NRF_RNG->TASKS_START = 1;
    while (NRF_RNG->EVENTS_VALRDY == 0) {};
    *value                 = (uint8_t)NRF_RNG->VALUE;
    NRF_RNG->EVENTS_VALRDY = 0;

    // Restore original config
    NRF_RNG->CONFIG = original_config;
}
