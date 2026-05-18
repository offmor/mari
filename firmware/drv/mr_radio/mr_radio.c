/**
 * @file
 * @ingroup drv_radio
 *
 * @brief  Generic definition of the "radio" module.
 *
 * @author Said Alvarado-Marin <said-alexander.alvarado-marin@inria.fr>
 * @author Geovane Fedrecheski <geovane.fedrecheski@inria.fr>
 *
 * @copyright Inria, 2025-now
 */

// #if defined(NRF5340_XXAA) && defined(NRF_APPLICATION)
// #include "mr_radio_nrf5340_app.c"
// #else
// #include "mr_radio_default.c"
// #endif

#if defined(NRF52840_XXAA) || (defined(NRF5340_XXAA) && defined(NRF_NETWORK))
#include "mr_radio_default.c"
#endif
