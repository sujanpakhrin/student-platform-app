# Student Management Platform

A three-tier application for adding, listing, retrieving, and deleting student records. Nginx serves the frontend, Flask provides the API, and MySQL stores the records in a named volume.

This repository contains the application source, Docker Compose configuration, and GitHub Actions workflow. The [infrastructure repository](https://github.com/sujanpakhrin/student-platform-infra) contains the Terraform configuration for AWS and EKS. The [GitOps repository](https://github.com/sujanpakhrin/student-platform-gitops) contains the Helm chart and Argo CD configuration.

## Run locally

From the repository root, create your local configuration:

```bash
cp .env.example .env
```

Set `DB_PASSWORD` and `DB_ROOT_PASSWORD` to two different values in `.env`. To generate each password, run `openssl rand -hex 24`. Keep `.env` out of Git.

Validate the configuration, build the images, and start the application:

```bash
docker compose config --quiet
docker compose up -d --build --wait
docker compose ps
curl -fsS http://localhost:8082/readyz
```

Open **http://localhost:8082**. If port `8082` is occupied, set `FRONTEND_PORT` in `.env` before starting Compose and use that port for both the browser and the readiness check.

## How a request reaches MySQL

1. The browser connects to Nginx through the frontend’s published port.
2. Nginx serves the page and forwards requests under `/api/` to Flask at `backend:5000`.
3. Flask reads or writes student records in MySQL at `database:3306` and returns the result through Nginx.

Compose provides DNS for the `backend` and `database` service names. Only Nginx publishes a host port. On first startup with an empty volume, MySQL runs [`database/init.sql`](database/init.sql) to create the `students` table.

## HTTP endpoints

| Method   | Endpoint             | Behaviour                                                               |
| -------- | -------------------- | ----------------------------------------------------------------------- |
| `GET`    | `/api/students`      | List student records.                                                   |
| `POST`   | `/api/students`      | Create a student from `name` and `email` and return the created record. |
| `GET`    | `/api/students/<id>` | Retrieve one student by ID.                                             |
| `DELETE` | `/api/students/<id>` | Delete one student by ID.                                               |
| `GET`    | `/readyz`            | Check the database connection and access to the `students` table.       |

## Student operations and persistence

To reproduce the browser demonstration:

1. Add two fictional students and confirm both appear in the list.
2. Select **View** for one student and note the ID. Delete the other student.
3. Recreate the containers while retaining the named MySQL volume:

   ```bash
   docker compose down
   docker compose up -d --wait
   ```

4. Refresh the browser. Confirm the student with the recorded ID is still present and the deleted student is still absent.

Use plain `docker compose down` for this test. Adding `-v` removes the named volume containing the records.

| Verification                                                                     | Recorded evidence                                                                     |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| All three services were running and the frontend port was published.             | [01 — Compose services and port mapping](docs/screenshots/01-compose-running.png)     |
| The browser displayed the student list and an individual record retrieved by ID. | [02 — Student list and details](docs/screenshots/02-student-list-and-details.png)     |
| The remaining record survived container recreation with the same volume.         | [03 — Student directory after restart](docs/screenshots/03-student-after-restart.png) |

## Continuous integration and published images

The [GitHub Actions workflow](.github/workflows/ci.yml) builds the frontend and backend images, starts the three-tier stack with Docker Compose, and tests student creation, listing, lookup, and deletion.

[Pull request #1](https://github.com/sujanpakhrin/student-platform-app/pull/1) passed validation before merge. The [publishing job on `main`](https://github.com/sujanpakhrin/student-platform-app/actions/runs/44477859858/job/135402652672) tested the merged application and pushed both images to Docker Hub.

**Build captured in the evidence:** `sha-4368a0d5f7701be833b04fdf62abcf7942c8c92f`. Both images carry this tag because they were built from the same application commit.

| Verification                                                                                                                                       | Recorded evidence                                                   |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| The pull request passed its build and API checks.                                                                                                  | [04 — Pull request checks](docs/screenshots/04-pr-checks.png)       |
| The workflow published both tested images after merge.                                                                                             | [05 — Publishing run on main](docs/screenshots/05-main-publish.png) |
| [`codeykenny/student-platform-frontend`](https://hub.docker.com/r/codeykenny/student-platform-frontend) contains the commit-tagged frontend image. | [06 — Frontend image tag](docs/screenshots/06-frontend-tag.png)     |
| [`codeykenny/student-platform-backend`](https://hub.docker.com/r/codeykenny/student-platform-backend) contains the matching backend image.         | [07 — Backend image tag](docs/screenshots/07-backend-tag.png)       |

## Troubleshooting

If startup or `/readyz` fails, check which service is unhealthy and read its recent logs:

```bash
docker compose ps -a
docker compose logs --tail=60 database backend frontend
```

If MySQL reports `Access denied` after you edit `.env`, check which credentials were used when the volume was initialized. MySQL retains its existing accounts when it starts with a populated volume. To keep the data, use the original credentials or update the MySQL account and application configuration together.
