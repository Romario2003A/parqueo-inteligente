# Sistema de Parqueo Inteligente
Sistema embebido bicéfalo: Raspberry Pi Zero 2W + Arduino UNO R3

## Descripción
Sistema que detecta vehículos, controla una barrera automática y detecta incendios,
publicando el estado en un dashboard web local en tiempo real.

## Hardware
- Raspberry Pi Zero 2W (supervisor)
- Arduino UNO R3 (nodo de campo)
- HC-SR04 (sensor distancia)
- Sound Sensor (sensor ruido)
- Flame Sensor IR (sensor incendio)
- Servo 9G (barrera)
- Buzzer, RGB LED, OLED SSD1306

## Comunicación
UART bidireccional via USB/OTG a 9600 baudios

## Ejecutar
```bash
cd ~/parqueo_inteligente
python3 supervisor.py
```
Dashboard: http://10.166.58.83:5000

## Curso
Arquitectura del Computador (24UC00147) - Universidad Continental - 2026
