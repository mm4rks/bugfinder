#!/bin/env bash

read -p "Install systemd services? [Y/n]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
    echo "skipping service registration"
    exit 0
fi

# systemd service unit file
worker_service_content="[Unit]
Description=Bugfinder dewolf worker
StartLimitIntervalSec=30
StartLimitBurst=2

[Service]
ExecStart=$(pwd)/worker.sh
WorkingDirectory=$(pwd)
Restart=on-failure
User=root

[Install]
WantedBy=multi-user.target"

echo "$worker_service_content" | sudo tee "/etc/systemd/system/bugfinder_worker.service" > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable "bugfinder_worker"
sudo systemctl start "bugfinder_worker"
sudo systemctl status "bugfinder_worker"

# web_service_content="[Unit]
# Description=Bugfinder webapp
# After=network.target
# StartLimitIntervalSec=30
# StartLimitBurst=2

# [Service]
# ExecStart=$(pwd)/web.sh
# WorkingDirectory=$(pwd)
# Restart=on-failure

# [Install]
# WantedBy=multi-user.target"

# echo "$web_service_content" | sudo tee "/etc/systemd/system/bugfinder_web.service" > /dev/null
# sudo systemctl daemon-reload
# sudo systemctl enable "bugfinder_web"
# sudo systemctl start "bugfinder_web"
# sudo systemctl status "bugfinder_web"


