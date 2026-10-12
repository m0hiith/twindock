# Always-on VM: Oracle Cloud Always Free, Docker, Mosquitto and HTTPS (Caddy)

For a TwinDock that never sleeps, use a small VM. Oracle Cloud's Always Free tier currently includes Ampere A1 Arm
instances (check the current terms; sign-up asks for a card for verification). The repository's
`deploy/vm/docker-compose.yml` runs three containers:
- `twindock`: the app;
- `mosquitto`: a password-protected broker, inside the compose network only;
- `caddy`: HTTPS with an automatic Let's Encrypt certificate.

## 1. The VM

1. In the Oracle Cloud console: **Compute → Instances → Create instance**.
   - Image: **Ubuntu 24.04**. Shape: **Ampere A1** (e.g. 2 OCPU, 12 GB; within the free allowance).
   - Add your SSH public key. Create.
2. **Networking → Virtual cloud networks →** your VCN **→ Security lists → Default →** add ingress rules for TCP
   **80** and **443** from `0.0.0.0/0`.
3. On the VM, also open the ports in Ubuntu's firewall (Oracle images ship iptables rules):

   ```sh
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
   sudo netfilter-persistent save
   ```

4. Point a DNS name at the VM's public IP: an `A` record for, say, `twindock.yourdomain.com`. A free subdomain from
   a dynamic-DNS provider works too.

## 2. Docker and the code

```sh
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git mosquitto-clients
sudo usermod -aG docker $USER && newgrp docker
git clone https://github.com/m0hiith/twindock.git && cd twindock    # a private repo needs a GitHub token or deploy key
```

## 3. Settings and the broker password

```sh
cp deploy/vm/env.example deploy/vm/.env
nano deploy/vm/.env            # DOMAIN=twindock.yourdomain.com, MQTT_BACKEND_PASSWORD=<a long random string>
# Mosquitto's password file, for the backend's user "twindock" (and later the board's):
docker run --rm -v "$PWD/deploy/vm:/w" eclipse-mosquitto:2 \
  mosquitto_passwd -b -c /w/passwd twindock "$(grep MQTT_BACKEND_PASSWORD deploy/vm/.env | cut -d= -f2)"
```

`deploy/vm/.env` and `deploy/vm/passwd` are git-ignored. Never commit them.

## 4. Start

```sh
docker compose --env-file deploy/vm/.env -f deploy/vm/docker-compose.yml up -d --build
docker compose -f deploy/vm/docker-compose.yml logs -f twindock    # warm start, then the 20 Hz loop
```

Open `https://twindock.yourdomain.com`; Caddy fetches the certificate on the first request. The historian is kept in
a Docker volume across restarts. `restart: unless-stopped` brings everything back after a reboot.

To update:

```sh
git pull && docker compose --env-file deploy/vm/.env -f deploy/vm/docker-compose.yml up -d --build
```

## 5. The real board on this VM (later)

The broker is deliberately not published to the internet. The board's firmware speaks plain MQTT, and its password
must not cross the internet in clear text. To let the board join from any Wi-Fi:

1. Add TLS to the firmware's MQTT client (WiSeConnect supports TLS; this is the "extra firmware work" the plan
   mentions).
2. Add a `listener 8883` with `certfile`/`keyfile` to `deploy/vm/mosquitto.conf`. Use a certificate for your
   domain (Caddy's, copied with read permission for the `mosquitto` user, or a separate Let's Encrypt certificate).
   Publish `8883:8883` on the `mosquitto` service and open TCP 8883 in the security list and iptables.
3. Add the board's own user to `passwd` and its broker settings to the firmware's secrets (never committed).

Until then, the VM runs the simulated factory and the real board stays with the laptop demo. The `twindock`
service sets `TWINDOCK_HOSTED=0` because a board *can* connect here. Set it to `auto` if you want the "Hosted demo"
banner while none does.
