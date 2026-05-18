/**
 * @file
 * @ingroup drv_gpio
 *
 * @brief  Definition of the "gpio" module.
 *
 * @author Alexandre Abadie <alexandre.abadie@inria.fr>
 * @author Geovane Fedrecheski <geovane.fedrecheski@inria.fr>
 *
 * @copyright Inria, 2025-now
 */
#include <nrf.h>
#include <assert.h>
#include <stdbool.h>
#include "mr_gpio.h"

//=========================== defines ==========================================

#define GPIOTE_MAX_CHANNELS (8U)

typedef struct {
    gpio_cb_t callback;
    void     *ctx;
} gpio_event_t;

typedef struct {
    uint8_t          gpiote_pin_idx;
    mr_gpio_t const *gpiote_pins[GPIOTE_MAX_CHANNELS];
    gpio_event_t     events[GPIOTE_MAX_CHANNELS];
} gpio_vars_t;

//=========================== variables ========================================

static gpio_vars_t _gpio_vars;

//=========================== public ===========================================

void mr_gpio_init(const mr_gpio_t *gpio, mr_gpio_mode_t mode) {

    // Reset the pin configuration
    mr_nrf_port[gpio->port]->PIN_CNF[gpio->pin] = 0;

    switch (mode) {
        case MR_GPIO_OUT:
            mr_nrf_port[gpio->port]->PIN_CNF[gpio->pin] |= GPIO_PIN_CNF_DIR_Output << GPIO_PIN_CNF_DIR_Pos;
            break;
        case MR_GPIO_IN:
            mr_nrf_port[gpio->port]->PIN_CNF[gpio->pin] &= ~(1UL << GPIO_PIN_CNF_INPUT_Pos);
            break;
        case MR_GPIO_IN_PU:
            mr_nrf_port[gpio->port]->PIN_CNF[gpio->pin] |= (GPIO_PIN_CNF_PULL_Pullup << GPIO_PIN_CNF_PULL_Pos);
            mr_nrf_port[gpio->port]->PIN_CNF[gpio->pin] &= ~(1UL << GPIO_PIN_CNF_INPUT_Pos);
            break;
        case MR_GPIO_IN_PD:
            mr_nrf_port[gpio->port]->PIN_CNF[gpio->pin] |= (GPIO_PIN_CNF_PULL_Pulldown << GPIO_PIN_CNF_PULL_Pos);
            mr_nrf_port[gpio->port]->PIN_CNF[gpio->pin] &= ~(1UL << GPIO_PIN_CNF_INPUT_Pos);
            break;
    }
}

void mr_gpio_init_irq(const mr_gpio_t *gpio, mr_gpio_mode_t mode, mr_gpio_irq_edge_t edge, gpio_cb_t callback, void *ctx) {
    uint8_t gpio_pin_idx = 0xff;
    for (uint8_t i = 0; i < _gpio_vars.gpiote_pin_idx; i++) {
        if (_gpio_vars.gpiote_pins[i] == gpio) {
            gpio_pin_idx = i;
        }
    }
    if (gpio_pin_idx == 0xff) {
        assert(_gpio_vars.gpiote_pin_idx < GPIOTE_MAX_CHANNELS);
        gpio_pin_idx                         = _gpio_vars.gpiote_pin_idx;
        _gpio_vars.gpiote_pins[gpio_pin_idx] = gpio;
        _gpio_vars.gpiote_pin_idx++;
    }

    _gpio_vars.events[gpio_pin_idx].callback = callback;
    _gpio_vars.events[gpio_pin_idx].ctx      = ctx;

    mr_gpio_init(gpio, mode);
    NVIC_EnableIRQ(GPIOTE_IRQn);

    NRF_GPIOTE->CONFIG[gpio_pin_idx] = (GPIOTE_CONFIG_MODE_Event << GPIOTE_CONFIG_MODE_Pos) |
                                       (gpio->pin << GPIOTE_CONFIG_PSEL_Pos) |
                                       (gpio->port << GPIOTE_CONFIG_PORT_Pos) |
                                       (edge << GPIOTE_CONFIG_POLARITY_Pos);
    NRF_GPIOTE->INTENSET |= (GPIOTE_INTENSET_IN0_Msk << gpio_pin_idx);
}

void mr_gpio_set(const mr_gpio_t *gpio) {
    mr_nrf_port[gpio->port]->OUTSET = (1 << gpio->pin);
}

void mr_gpio_clear(const mr_gpio_t *gpio) {
    mr_nrf_port[gpio->port]->OUTCLR = (1 << gpio->pin);
}

void mr_gpio_toggle(const mr_gpio_t *gpio) {
    mr_nrf_port[gpio->port]->OUT ^= (1 << gpio->pin);
}

uint8_t mr_gpio_read(const mr_gpio_t *gpio) {
    if (mr_nrf_port[gpio->port]->DIR & (1 << gpio->pin)) {
        return (mr_nrf_port[gpio->port]->OUT & (1 << gpio->pin)) ? 1 : 0;
    } else {
        return (mr_nrf_port[gpio->port]->IN & (1 << gpio->pin)) ? 1 : 0;
    }
}

void GPIOTE_IRQHandler(void) {
    for (uint8_t i = 0; i < _gpio_vars.gpiote_pin_idx; ++i) {
        if (NRF_GPIOTE->EVENTS_IN[i] == 1) {
            NRF_GPIOTE->EVENTS_IN[i] = 0;
            _gpio_vars.events[i].callback(_gpio_vars.events[i].ctx);
            break;
        }
    }
}
