#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
#include <nrfx_timer.h>
#include <nrfx_gpiote.h>

LOG_MODULE_REGISTER(uart_intercept, LOG_LEVEL_INF);

#define RX_PIN 10

static struct gpio_dt_spec rx_dt = {.port = DEVICE_DT_GET(DT_NODELABEL(gpio0)), .pin = RX_PIN, .dt_flags = GPIO_PULL_UP};
static struct gpio_dt_spec tx_dt = {.port = DEVICE_DT_GET(DT_NODELABEL(gpio1)), .pin = 10};

#define GPIOTE_INST 0
#define GPIOTE_NODE DT_NODELABEL(_CONCAT(gpiote, GPIOTE_INST))
const nrfx_gpiote_t gpiote = NRFX_GPIOTE_INSTANCE(GPIOTE_INST);

void on_softserial_frame_tick(nrf_timer_event_t event_type, void *p_context);
#define SOFTSERIAL_TIMER_IDX 0
#define SOFTSERIAL_BAUDRATE 9600

nrfx_timer_t softserial_timer_inst = NRFX_TIMER_INSTANCE(SOFTSERIAL_TIMER_IDX);
nrfx_timer_config_t softserial_timer_config = {
    .frequency = NRF_TIMER_BASE_FREQUENCY_GET(timer_inst.p_reg),
    .bit_width = NRF_TIMER_BIT_WIDTH_16,
    .interrupt_priority = DT_IRQ(DT_NODELABEL(timer0), priority),
    .mode = NRF_TIMER_MODE_TIMER};

static uint8_t word;
static uint8_t length;
static uint8_t ticks;

void on_softserial_frame_tick(nrf_timer_event_t event_type, void *p_context)
{
        ticks++;
        uint8_t pin_state = gpio_pin_get_raw(rx_dt.port, rx_dt.pin);
        switch (ticks)
        {
        case 1:
                if (pin_state)
                {
                        nrfx_gpiote_trigger_enable(&gpiote, RX_PIN, true);
                        nrfx_timer_disable(&softserial_timer_inst);
                }
                break;
        case 3:
                word |= pin_state;
                break;
        case 5:
                word |= pin_state << 1;
                break;
        case 7:
                word |= pin_state << 2;
                break;
        case 9:
                word |= pin_state << 3;
                break;
        case 11:
                word |= pin_state << 4;
                break;
        case 13:
                word |= pin_state << 5;
                break;
        case 15:
                word |= pin_state << 6;
                break;
        case 17:
                word |= (pin_state << 7);
                printk("%02x ", word);
                nrfx_gpiote_trigger_enable(&gpiote, RX_PIN, true);
                nrfx_timer_disable(&softserial_timer_inst);
                break;
        }
}

void on_rx_fall(nrfx_gpiote_pin_t pin_type, nrfx_gpiote_trigger_t event_type, void *p_context)
{
        nrfx_gpiote_trigger_disable(&gpiote, RX_PIN);
        nrfx_timer_enable(&softserial_timer_inst);
        word = 0;
        ticks = 0;
        length = 0;
}

int main(void)
{
        int ret;

        IRQ_CONNECT(DT_IRQN(DT_NODELABEL(timer0)), DT_IRQ(DT_NODELABEL(timer0), priority),
                    NRFX_TIMER_INST_HANDLER_GET(SOFTSERIAL_TIMER_IDX), 0, 0);

        if (!gpio_is_ready_dt(&rx_dt) || !gpio_is_ready_dt(&tx_dt))
        {
                LOG_ERR("button device is not ready");
                return 0;
        }

        ret = gpio_pin_configure_dt(&rx_dt, GPIO_INPUT | GPIO_ACTIVE_LOW);
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

        if (ret != 0)
        {
                printk("failed to configure interrupt: %d", ret);
                return 0;
        }

        nrfx_err_t status = nrfx_timer_init(&softserial_timer_inst, &softserial_timer_config, on_softserial_frame_tick);
        NRFX_ASSERT(status == NRFX_SUCCESS);
        status = nrfx_gpiote_init(&gpiote, 0);
        NRFX_ASSERT(status == NRFX_SUCCESS);

        /* Initialize input pin to generate event on high to low transition
         * (falling edge) and call button_handler()
         */
        static const nrf_gpio_pin_pull_t pull_config = NRF_GPIO_PIN_PULLUP;
        nrfx_gpiote_trigger_config_t trigger_config = {
            .trigger = NRFX_GPIOTE_TRIGGER_HITOLO,
        };
        static const nrfx_gpiote_handler_config_t handler_config = {
            .handler = on_rx_fall,
        };
        nrfx_gpiote_input_pin_config_t input_config = {
            .p_pull_config = &pull_config,
            .p_trigger_config = &trigger_config,
            .p_handler_config = &handler_config};
        status = nrfx_gpiote_input_configure(&gpiote, rx_dt.pin, &input_config);
        NRFX_ASSERT(status == NRFX_SUCCESS);

        nrfx_timer_clear(&softserial_timer_inst);
        /*
         * Setting the timer channel NRF_TIMER_CC_CHANNEL0 in the extended compare mode to stop the timer and
         * trigger an interrupt if internal counter register is equal to desired_ticks.
         */
        nrfx_timer_extended_compare(&softserial_timer_inst, NRF_TIMER_CC_CHANNEL0, nrfx_timer_us_to_ticks(&softserial_timer_inst, USEC_PER_SEC / SOFTSERIAL_BAUDRATE / 2),
                                    NRF_TIMER_SHORT_COMPARE0_CLEAR_MASK, true);

        nrfx_gpiote_trigger_enable(&gpiote, RX_PIN, true);

        printk("Set up rx at %s low pin %d\n", rx_dt.port->name, rx_dt.pin);

        return 0;
}
