# Lab setup

- [1. Required steps](#1-required-steps)
  - [1.1. Clean up Lab 4 on your VM](#11-clean-up-lab-4-on-your-vm)
  - [1.2. Set up your fork on `GitHub`](#12-set-up-your-fork-on-github)
    - [1.2.1. Fork the course instructors' repo](#121-fork-the-course-instructors-repo)
    - [1.2.2. Go to your fork](#122-go-to-your-fork)
    - [1.2.3. Enable issues](#123-enable-issues)
    - [1.2.4. Add a classmate as a collaborator](#124-add-a-classmate-as-a-collaborator)
    - [1.2.5. Protect your `main` branch](#125-protect-your-main-branch)
  - [1.3. Clone your fork and configure the local environment](#13-clone-your-fork-and-configure-the-local-environment)
  - [1.4. Start the services locally](#14-start-the-services-locally)
  - [1.5. Deploy to your VM](#15-deploy-to-your-vm)
    - [1.5.1. Connect to your VM and clone the repo](#151-connect-to-your-vm-and-clone-the-repo)
    - [1.5.2. Configure the environment on the VM](#152-configure-the-environment-on-the-vm)
    - [1.5.3. Start the services on the VM](#153-start-the-services-on-the-vm)
  - [1.6. Verify the deployment](#16-verify-the-deployment)
  - [1.7. Set up a coding agent](#17-set-up-a-coding-agent)
  - [1.8. Set up the autochecker](#18-set-up-the-autochecker)

## 1. Required steps

> [!NOTE]
> This lab builds on the same tools and setup from Lab 4.
> If you completed Lab 4, most tools are already installed.
> The main changes are: a new repo, `Autochecker` API credentials for the ETL pipeline, and a fresh deployment for Lab 5.

> [!NOTE]
> This lab uses your university email, `GitHub` username, `Telegram` alias, and VM IP in the autochecker bot.
> If you have not registered them yet, do that in [step 1.8](#18-set-up-the-autochecker).

### 1.1. Clean up Lab 4 on your VM

> [!IMPORTANT]
> Remove Lab 4 containers and volumes to free ports and disk space on your VM before deploying Lab 5.

1. [Connect to your VM](../../wiki/ssh.md#connect-to-the-vm).
2. To go to the Lab 4 project directory,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cd ~/se-toolkit-lab-4
   ```

3. To stop and remove the Lab 4 containers and volumes,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret down -v
   ```

4. To go back to your home directory,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cd ~
   ```

> [!TIP]
> If `~/se-toolkit-lab-4` does not exist on the VM, you can skip this step.

### 1.2. Set up your fork on `GitHub`

#### 1.2.1. Fork the course instructors' repo

1. [Fork the course instructors' repo](../../wiki/github.md#fork-a-repo).

   The course instructors' repo URL is <https://github.com/inno-se-toolkit/se-toolkit-lab-5>.

We refer to your fork as `fork` and to the original repo as `upstream`.

#### 1.2.2. Go to your fork

1. [Go to your fork](../../wiki/github.md#go-to-your-fork).

   The URL of your fork should look like `https://github.com/<your-github-username>/se-toolkit-lab-5`.

#### 1.2.3. Enable issues

1. [Enable issues](../../wiki/github.md#enable-issues).

#### 1.2.4. Add a classmate as a collaborator

1. [Add a collaborator](../../wiki/github.md#add-a-collaborator) — your partner.
2. Your partner should add you as a collaborator in their repo.

#### 1.2.5. Protect your `main` branch

1. [Protect the `main` branch](../../wiki/github.md#protect-a-branch).

### 1.3. Clone your fork and configure the local environment

1. To clone your fork on your computer,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   git clone https://github.com/<your-github-username>/se-toolkit-lab-5.git
   ```

2. [Open in `VS Code` the directory](../../wiki/vs-code.md#open-the-directory):
   `se-toolkit-lab-5`.
3. [Check the current shell in the `VS Code Terminal`](../../wiki/vs-code.md#check-the-current-shell-in-the-vs-code-terminal).
4. To install the `Python` dependencies,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   uv sync --dev
   ```

5. To create the [`Docker Compose` environment file](../../wiki/dotenv-docker-secret.md#what-is-envdockersecret),

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cp .env.docker.example .env.docker.secret
   ```

6. Open [`.env.docker.secret`](../../wiki/dotenv-docker-secret.md#what-is-envdockersecret).
7. Set [`AUTOCHECKER_EMAIL`](../../wiki/dotenv-docker-secret.md#autochecker_email) to your university email.
8. Set [`AUTOCHECKER_PASSWORD`](../../wiki/dotenv-docker-secret.md#autochecker_password) to `<your-github-username><your-telegram-alias>`.

   Example: if your `GitHub` username is `johndoe` and your `Telegram` alias is `jdoe`, the password is `johndoejdoe`.

9. Set [`API_KEY`](../../wiki/dotenv-docker-secret.md#api_key) to a secret value that you will use in [`Swagger UI`](../../wiki/swagger.md#authorize-in-swagger-ui).

> [!IMPORTANT]
> The values of [`AUTOCHECKER_EMAIL`](../../wiki/dotenv-docker-secret.md#autochecker_email) and [`AUTOCHECKER_PASSWORD`](../../wiki/dotenv-docker-secret.md#autochecker_password) must match your autochecker bot registration.

> [!TIP]
> Unless you have a reason to change them, keep the default values of [`CADDY_HOST_PORT`](../../wiki/dotenv-docker-secret.md#caddy_host_port), [`PGADMIN_HOST_PORT`](../../wiki/dotenv-docker-secret.md#pgadmin_host_port), and the database settings.

### 1.4. Start the services locally

1. [Start `Docker`](../../wiki/docker.md#start-docker).
2. To start the services in the background,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret up --build -d
   ```

3. To check that the containers are running,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret ps --format "table {{.Service}}\t{{.Status}}"
   ```

   You should see all four services running with status `Up`:

   ```terminal
   SERVICE    STATUS
   app        Up 50 seconds
   caddy      Up 49 seconds
   pgadmin    Up 50 seconds
   postgres   Up 55 seconds (healthy)
   ```

4. Open `http://127.0.0.1:42002/docs` in a browser.

   If you changed [`CADDY_HOST_PORT`](../../wiki/dotenv-docker-secret.md#caddy_host_port) in [`.env.docker.secret`](../../wiki/dotenv-docker-secret.md#what-is-envdockersecret), use your value instead of `42002`.

5. [Authorize in `Swagger UI`](../../wiki/swagger.md#authorize-in-swagger-ui) with your [`API_KEY`](../../wiki/dotenv-docker-secret.md#api_key).

> [!NOTE]
> The database starts empty in this lab.
> You will populate it in [Task 1](./required/task-1.md#14-part-b-build-the-pipeline) by calling `POST /pipeline/sync`.

<details><summary><b>Troubleshooting (click to open)</b></summary>

<h4>Port conflict (<code>port is already allocated</code>)</h4>

[Clean up `Docker`](../../wiki/docker.md#clean-up-docker), then run the `docker compose up` command again.

<h4>Containers exit immediately</h4>

To rebuild all containers from scratch,

[run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

```terminal
docker compose --env-file .env.docker.secret down -v
docker compose --env-file .env.docker.secret up --build -d
```

</details>

### 1.5. Deploy to your VM

#### 1.5.1. Connect to your VM and clone the repo

1. [Connect to your VM](../../wiki/ssh.md#connect-to-the-vm).
2. To clone your fork on the VM,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   git clone https://github.com/<your-github-username>/se-toolkit-lab-5.git ~/se-toolkit-lab-5
   ```

3. To go to the project directory on the VM,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cd ~/se-toolkit-lab-5
   ```

#### 1.5.2. Configure the environment on the VM

1. To create the VM copy of [`.env.docker.secret`](../../wiki/dotenv-docker-secret.md#what-is-envdockersecret),

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cp .env.docker.example .env.docker.secret
   ```

2. To open the environment file for editing,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   nano .env.docker.secret
   ```

3. Set [`AUTOCHECKER_EMAIL`](../../wiki/dotenv-docker-secret.md#autochecker_email) to the same value as on your computer.
4. Set [`AUTOCHECKER_PASSWORD`](../../wiki/dotenv-docker-secret.md#autochecker_password) to the same value as on your computer.
5. Set [`API_KEY`](../../wiki/dotenv-docker-secret.md#api_key) to the same value as on your computer, or choose another value that you will remember for VM testing.
6. Save the file and exit `nano`.

> [!TIP]
> In `nano`, press `Ctrl+X`, then `Y`, then `Enter` to save and exit.

#### 1.5.3. Start the services on the VM

1. To start the services on the VM in the background,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret up --build -d
   ```

2. To check that the containers are running on the VM,

   [run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose --env-file .env.docker.secret ps --format "table {{.Service}}\t{{.Status}}"
   ```

   You should see all four services running with status `Up`.

<details><summary><b>Troubleshooting (click to open)</b></summary>

<h4>Port conflict (<code>port is already allocated</code>)</h4>

On the VM, stop the old Lab 4 deployment first. See [step 1.1](#11-clean-up-lab-4-on-your-vm).

<h4>Containers exit immediately</h4>

To rebuild all containers from scratch on the VM,

[run in the `VS Code Terminal`](../../wiki/vs-code.md#run-a-command-in-the-vs-code-terminal):

```terminal
docker compose --env-file .env.docker.secret down -v
docker compose --env-file .env.docker.secret up --build -d
```

</details>

### 1.6. Verify the deployment

1. Open `http://<your-vm-ip-address>:<caddy-port>/docs` in a browser.

   Replace:

   - [`<your-vm-ip-address>`](../../wiki/vm.md#your-vm-ip-address).
   - `<caddy-port>` with the value of [`CADDY_HOST_PORT`](../../wiki/dotenv-docker-secret.md#caddy_host_port) in [`.env.docker.secret`](../../wiki/dotenv-docker-secret.md#what-is-envdockersecret) (default: `42002`).

   Example: `http://192.0.2.1:42002/docs`.

2. [Authorize in `Swagger UI`](../../wiki/swagger.md#authorize-in-swagger-ui) with your [`API_KEY`](../../wiki/dotenv-docker-secret.md#api_key).
3. Try `GET /items/`.

   You should get an empty array `[]`.

> [!NOTE]
> Seeing `[]` here is expected.
> The ETL pipeline that populates the database is implemented later in [Task 1](./required/task-1.md#14-part-b-build-the-pipeline).

### 1.7. Set up a coding agent

A coding agent will help you implement the ETL pipeline, analytics endpoints, and dashboard faster.

<!-- no toc -->
- Method 1: [Set up `Qwen Code`](../../wiki/qwen.md#set-up-qwen-code).
- Method 2: [Choose another coding agent](../../wiki/coding-agents.md#choose-and-use-a-coding-agent).

### 1.8. Set up the autochecker

1. [Set up the autochecker](../../wiki/autochecker.md#set-up-the-autochecker).
2. Make sure your university email, `GitHub` username, and VM IP are registered in the bot.

---

You are ready to start the lab tasks.
Continue with [Task 1](./required/task-1.md).
