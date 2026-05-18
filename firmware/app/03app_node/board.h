/**
 * @file
 * @brief       Generic board support interface.
 * @details
 *
 */
#ifndef BOARD_H
#define BOARD_H

#include <stdint.h>

typedef enum {
    OFF,
    RED,
    GREEN,
    BLUE,
    PURPLE,
    YELLOW,
    CYAN,
    MAGENTA,
    ORANGE,
    PINK,
    WHITE,
} led_color_t;

void board_init(void);
void board_set_led_mari_gateway(uint64_t gateway_id);
void board_set_led_mari(led_color_t color);
void board_set_led_app(led_color_t color);

#endif
