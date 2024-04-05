#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
#include <zephyr/irq.h>
#include <inttypes.h>

LOG_MODULE_REGISTER(uart_intercept, LOG_LEVEL_INF);

#define GPIOTE_INST 0
#define GPIOTE_NODE DT_NODELABEL(_CONCAT(gpiote, GPIOTE_INST))
#define RX_LOW_PIN 10
#define RX_HIGH_PIN 9

static struct gpio_dt_spec rx_low_dt = {.port = DEVICE_DT_GET(DT_NODELABEL(gpio0)), .pin = RX_LOW_PIN, .dt_flags = GPIO_PULL_DOWN};
static struct gpio_dt_spec rx_high_dt = {.port = DEVICE_DT_GET(DT_NODELABEL(gpio0)), .pin = RX_HIGH_PIN};
static struct gpio_dt_spec tx_dt = {.port = DEVICE_DT_GET(DT_NODELABEL(gpio1)), .pin = 10};
static struct gpio_callback rx_low_cb_data;
static struct gpio_callback rx_high_cb_data;
static uint32_t rx_k_cycles_prev = 0;

void on_rx_high(const struct device *dev, struct gpio_callback *cb,
                uint32_t pins)
{
        uint32_t rx_k_cycles = k_cycle_get_32();
        uint32_t delta = rx_k_cycles - rx_k_cycles_prev;
        rx_k_cycles_prev = k_cycle_get_32();
        delta/=3;
        for (; delta > 0; delta--)
        {
                putchar('.');
        }
}

void on_rx_low(const struct device *dev, struct gpio_callback *cb,
               uint32_t pins)
{
        uint32_t rx_k_cycles = k_cycle_get_32();
        uint32_t delta = rx_k_cycles - rx_k_cycles_prev;
        rx_k_cycles_prev = k_cycle_get_32();
        delta/=3;
        for (; delta > 0; delta--)
        {
                putchar('X');
        }
}

int main(void)
{
        int ret;

        if (!gpio_is_ready_dt(&rx_low_dt) || !gpio_is_ready_dt(&rx_high_dt) || !gpio_is_ready_dt(&tx_dt))
        {
                LOG_ERR("button device is not ready");
                return 0;
        }

        ret = gpio_pin_configure_dt(&rx_low_dt, GPIO_INPUT | GPIO_ACTIVE_LOW);
        if (ret != 0)
        {
                LOG_ERR("failed to configure pin: %d", ret);
                return 0;
        }

        ret = gpio_pin_configure_dt(&rx_high_dt, GPIO_INPUT | GPIO_ACTIVE_LOW);
        if (ret != 0)
        {
                LOG_ERR("failed to configure pin: %d", ret);
                return 0;
        }

        ret = gpio_pin_configure_dt(&tx_dt, GPIO_OUTPUT);
        if (ret != 0)
        {
                LOG_ERR("failed to configure pin: %d", ret);
                return 0;
        }

        ret = gpio_pin_interrupt_configure_dt(&rx_low_dt,
                                              GPIO_INT_EDGE_TO_ACTIVE);
        if (ret != 0)
        {
                printk("failed to configure interrupt: %d", ret);
                return 0;
        }

        ret = gpio_pin_interrupt_configure_dt(&rx_high_dt,
                                              GPIO_INT_EDGE_TO_INACTIVE);
        if (ret != 0)
        {
                printk("failed to configure interrupt: %d", ret);
                return 0;
        }

        gpio_init_callback(&rx_low_cb_data, on_rx_low, BIT(rx_low_dt.pin));
        gpio_init_callback(&rx_high_cb_data, on_rx_high, BIT(rx_high_dt.pin));
        gpio_add_callback(rx_low_dt.port, &rx_low_cb_data);
        gpio_add_callback(rx_high_dt.port, &rx_high_cb_data);
        rx_k_cycles_prev = k_cycle_get_32();
        printk("Set up rx at %s low pin %d, high pin %d\n", rx_low_dt.port->name, rx_low_dt.pin, rx_high_dt.pin);

        return 0;
}
