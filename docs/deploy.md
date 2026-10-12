# Deploying TwinDock

TwinDock's backend is one long-running process: a 20 Hz loop, an in-memory world, the site simulator and a
WebSocket hub. It must run as **one always-on container with exactly one worker**, never as serverless functions
(why: [deploy_diagnosis.md](deploy_diagnosis.md)). The `Dockerfile` builds that container. It serves the built
frontend, `/api` and `/ws` on `$PORT` (7860 by default).

On a hosted deploy there is no broker, so every value is simulated. The page says so with a "Hosted demo" banner,
and the real SiWx917 board is shown in the live demo from your laptop. When the container starts, or when a free
host wakes it up, it fast-forwards 45 simulated minutes (about 7–10 s) so the factory is already running.

| Option | Cost | Good for | Catch |
|---|---|---|---|
| Hugging Face Spaces (Docker) | free | the public link for recruiters | sleeps when unused (about 48 h on free hardware; check the Space's settings) and restarts the simulation on wake |
| Render (free web service) | free | Git-based deploys from the private GitHub repo | sleeps after ~15 min idle; ~1 min to wake |
| Oracle Cloud Always Free VM | free (card check) | truly always on, with a broker | more setup: [deploy_vm.md](deploy_vm.md) |
| Your laptop | free | the live demo with the real board | only while the laptop is on |

## 0. Run the container locally first

You need Docker. On this Mac it is Colima plus the Homebrew docker CLI: `brew install colima docker docker-buildx`, then `colima start`.

```sh
cd "<repo>"
docker build -t twindock .
docker run --rm -p 7860:7860 twindock
```

Open http://localhost:7860. To check it is alive for a while (auto mode, compressor, generator, line, vibration):

```sh
.venv/bin/python scripts/verify_live.py http://localhost:7860 --minutes 10
```

Health: http://localhost:7860/api/health shows the uptime, the tick rate achieved, the simulation clock, the warm
start and the SIM devices online.

## 1. Hugging Face Spaces (the public link)

Click by click:

1. Sign in at https://huggingface.co (create a free account if needed).
2. Top right, click your avatar → **New Space** (or go to https://huggingface.co/new-space).
3. Fill in:
   - **Owner**: you. **Space name**: `twindock`.
   - **Short description**: optional (the README sets one).
   - **License**: whatever you prefer (for example `other` if unsure).
   - **Select the Space SDK**: **Docker** → template **Blank**.
   - **Space hardware**: **CPU basic · 2 vCPU · 16 GB · FREE**.
   - **Visibility**: **Public** (so recruiters can open it).
4. Click **Create Space**. Leave the page open; it shows an empty Space.
5. Make a write token: avatar → **Settings** → **Access Tokens** → **Create new token** → token type **Write** →
   name it `twindock-push` → **Create token** → **copy it** (you won't see it again).
6. On your Mac, once: `brew install git-lfs` (the Space stores the logo PNG with Git LFS).
7. From the repository root:

   ```sh
   HF_SPACE=<your-hf-username>/twindock ./scripts/push_hf_space.sh
   ```

   When git asks, the username is your Hugging Face username and the **password is the token** from step 5.
   The script pushes one fresh commit of the current `HEAD`. It contains only committed files, never `.env`. It
   swaps in the Space's README (`deploy/huggingface/README.md`, with `sdk: docker` and `app_port: 7860`), so your
   project README stays as it is.
8. Back on the Space page, open the **Logs** tab and watch the build. It installs the frontend, builds it, installs
   the backend and starts. It shows **Running** after a few minutes.
9. Open the **App** tab. Your public link is `https://<your-hf-username>-twindock.hf.space`.
   - The bottom of every page shows the "Hosted demo" banner.
   - The top bar shows the simulation clock with ×1 / ×5 / ×20.
   - `/model` shows how the simulation works.
10. To update later, commit as usual, then run step 7 again.

Optional settings: Space → **Settings** → **Variables and secrets**. `TZ` changes the site's time zone (default
`Asia/Kolkata`). Never put secrets in the repository; if you later connect a cloud broker, add `MQTT_URL` here as
a **secret**.

## 2. Render (the alternative)

Render builds straight from the private GitHub repo using `render.yaml`.

1. Sign in at https://dashboard.render.com with GitHub.
2. Top right **New +** → **Blueprint**.
3. **Connect a repository**: if `m0hiith/twindock` isn't listed, click **Configure account**, give Render's GitHub
   app access to that repository, and come back.
4. Select `m0hiith/twindock`, branch `master`. Render reads `render.yaml`: one **web service**, runtime **Docker**,
   plan **Free**, health check `/api/health`.
5. Give the Blueprint a name (for example `twindock`) and click **Apply**.
6. Open the service. The **Events** and **Logs** tabs show the Docker build, then `warm start: 2700 simulated s in …`,
   then the service goes **Live**.
7. Your link is shown at the top: `https://twindock.onrender.com` (or a suffixed name if that one is taken).
8. Free services sleep after about 15 minutes without visitors. The first visit after that takes about a minute
   (container start + warm start); the factory is then already running.
9. Every push to `master` redeploys automatically (`autoDeploy: true`). To pause that, turn off **Auto-Deploy** in
   the service's **Settings**.

## 3. The live demo with the real board (laptop)

This is the setup from the README: Mosquitto on the laptop, the board on the same Wi-Fi, and the backend and
frontend in development mode (or `docker run -e MQTT_URL=mqtt://host.docker.internal:1883 -p 7860:7860 twindock`
with the laptop's Mosquitto). With a broker configured the "Hosted demo" banner is off, the board shows LIVE, and the
simulation speed stays at ×1 while the board is online.

To show the laptop to someone remotely, a Cloudflare quick tunnel works without an account:

```sh
brew install cloudflared
cloudflared tunnel --url http://localhost:7860
```

It prints a temporary `https://….trycloudflare.com` link; it lasts as long as the command runs.

## Environment variables

| Variable | Default (container) | What |
|---|---|---|
| `PORT` | 7860 | the port to listen on (Render sets 10000) |
| `MQTT_URL` | unset | `mqtt://user:pass@host:1883` or `mqtts://user:pass@host:8883`: connect to that broker (e.g. HiveMQ Cloud) so a real board can join. A **secret**: set it in the host's dashboard, never in the repo |
| `TWINDOCK_MQTT` | 0 | `1` to use the local broker from `TWINDOCK_MQTT_HOST`/`PORT` |
| `TWINDOCK_SIM` | auto | `embedded` / `external`: where the site simulator runs |
| `TWINDOCK_WARM_START_MIN` | 45 | simulated minutes fast-forwarded at start; `0` to switch off |
| `TWINDOCK_SEED` | date-based | fix the simulation seed |
| `TWINDOCK_HOSTED` | auto | the "Hosted demo" banner (`auto`: on when nothing real can connect) |
| `TWINDOCK_HISTORIAN_DB` | `backend/data/historian.sqlite` | the historian's SQLite file (24 simulated hours kept) |
| `TZ` | Asia/Kolkata | the site's time zone (solar, shifts, tariffs) |
| `TWINDOCK_PACE` | 2.5 | the warehouse's demo pace (`1` = real speed) |
