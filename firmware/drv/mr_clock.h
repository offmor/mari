#ifndef __MR_CLOCK_H
#define __MR_CLOCK_H

/**
 * @defgroup    bsp_clock   Clock
 * @ingroup     bsp
 * @brief       Functions to initialize low and high frequency clocks
 *
 * @{
 * @file
 * @author Alexandre Abadie <alexandre.abadie@inria.fr>
 * @copyright Inria, 2022
 * @}
 */

#if defined(NRF5340_XXAA)
#if defined(NRF_NETWORK) || defined(NRF_TRUSTZONE_NONSECURE)
#define NRF_CLOCK NRF_CLOCK_NS
#else
#define NRF_CLOCK NRF_CLOCK_S
#endif
#endif

/**
 * @brief Initialize and start the High Frequency clock
 */
void mr_hfclk_init(void);

/**
 * @brief Initialize and start the Low Frequency clock
 */
void mr_lfclk_init(void);

#endif /* __MR_CLOCK_H */
