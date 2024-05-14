#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
#include "softserial.h"

LOG_MODULE_REGISTER(uart_intercept, LOG_LEVEL_INF);

static struct gpio_dt_spec tx_dt = {.port = DEVICE_DT_GET(DT_NODELABEL(gpio1)), .pin = 10};




int main(void)
{
        int ret;

        softserial_init();


        if (!gpio_is_ready_dt(&tx_dt))
        {
                LOG_ERR("button device is not ready");
                return 0;
        }

        ret = gpio_pin_configure_dt(&tx_dt, GPIO_OUTPUT);
        if (ret != 0)
        {
                LOG_ERR("failed to configure pin: %d", ret);
                return 0;
        }

        softserial_start();

        return 0;
}
