#ifndef SOFTSERIAL_H__
#define SOFTSERIAL_H__

typedef enum 
{
    SOFTSERIAL_ERROR_GPIO_NOT_READY,
    SOFTSERIAL_ERROR_SIZE
} softserial_error_t;

softserial_error_t softserial_init();
void softserial_start();

#endif // SOFTSERIAL_H__