# Guía de Instalación - Sistema de Cartelería Digital Raspberry Pi 3 A+

## Requisitos

* **Raspberry Pi 3 A+**

* Raspberry Pi OS Lite instalado

* SSH habilitado

* Conexión a internet

> Para instalación del OS: [Guía oficial](https://www.raspberrypi.com/software/)

## Instalación

### 1. Actualizar Sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-dev git curl vlc ffmpeg
sudo reboot
```

### 2. Instalar UV

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### 3. Configurar Proyecto

```bash
cd ~
git clone <URL_REPOSITORIO> kdx-pi-signage
cd kdx-pi-signage
uv sync
mkdir -p videos
```

### 4. Crear Servicio

```bash
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/kdx-signage.service <<EOF
[Unit]
Description=KDX Digital Signage
After=graphical-session.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/kdx-pi-signage
Environment=DISPLAY=:0
ExecStart=/home/pi/.local/bin/uv run python main.py
Restart=always

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable kdx-signage.service
sudo loginctl enable-linger pi
systemctl --user start kdx-signage.service
```

### 5. Auto-login

```bash
sudo raspi-config nonint do_boot_behaviour B4
```

### 6. Optimizar GPU

```bash
echo 'gpu_mem=64' | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

## Verificación

```bash
systemctl --user status kdx-signage.service
journalctl --user -u kdx-signage.service -f
```

