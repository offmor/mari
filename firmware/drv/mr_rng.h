#ifndef __MR_RNG_H
#define __MR_RNG_H

/**
 * @brief       Read the RNG peripheral
 *
 * @{
 * @file
 * @author Alexandre Abadie <alexandre.abadie@inria.fr>
 * @copyright Inria, 2024
 * @}
 */

#include <stdint.h>

//=========================== defines ==========================================

//=========================== prototypes =======================================

/**
 * @brief Configure the random number generator (RNG)
 */
void mr_rng_init(void);

/**
 * @brief Read a random value (8 bits)
 *
 * @param[out] value address of the output value
 */
void mr_rng_read_u8(uint8_t *value);

void mr_rng_read_u8_fast(uint8_t *value);

void mr_rng_read_u16(uint16_t *value);

void mr_rng_read_range(uint8_t *value, uint8_t min, uint8_t max);

#endif  // __MR_RNG_H
