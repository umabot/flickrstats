# GCP Deployment & Operations

This document captures the **live Google Cloud configuration** for the Flickr stats project and provides the main `gcloud` / `bq` commands used to inspect and operate it.

> For local Python usage and general project setup, see [`README.md`](./README.md).
>
> All command output below was captured on **2026-04-06** and may change over time.

---

## Project reference

| Item | Value |
|---|---|
| GCP project ID | `flickrstats-492309` |
| Project name | `FlickrStats` |
| Project number | `781796249121` |
| Cloud Function | `flickr-daily-extract` |
| Entry point | `main_handler` |
| Runtime | `python311` |
| Function service account | `flickr-stats-loader@flickrstats-492309.iam.gserviceaccount.com` |
| BigQuery dataset | `flickrstats` |
| Stage table | `flickrstats-492309.flickrstats.stage_daily_extract` |
| Target table | `flickrstats-492309.flickrstats.flickrstats_all` |

## Region layout

This project currently uses **more than one European region**:

| Service | Region / Location | Evidence |
|---|---|---|
| BigQuery dataset | `europe-west9` | Verified with `bq show` |
| Cloud Function | `europe-west9` | Verified with `gcloud functions list` |
| Cloud Run service | `europe-west9` | Verified with `gcloud run services list` |
| Cloud Scheduler job | `europe-west1` | Verified with `gcloud scheduler jobs list --location=europe-west1` |

> `europe-west9` is where the BigQuery dataset is located, while some operational services such as Cloud Scheduler are running in `europe-west1` (Brussels).

---

## 1) Set and verify the active project

### Command

```bash
gcloud config set project flickrstats-492309
gcloud config list --format='text(core.account,core.project)'
```

### Captured output

```text
WARNING: Your active project does not match the quota project in your local Application Default Credentials file. This might result in unexpected quota issues.

To update your Application Default Credentials quota project, use the `gcloud auth application-default set-quota-project` command.
[environment: untagged] Read more to tag: g.co/cloud/project-env-tag.
Updated property [core/project].

account: silvio@innovumabot.com
project: flickrstats-492309
```

---

## 2) Describe the project

### Command

```bash
gcloud projects describe flickrstats-492309 \
  --format='yaml(projectId,projectNumber,name,lifecycleState,createTime)'
```

### Captured output

```yaml
createTime: '2026-04-04T09:21:54.762Z'
lifecycleState: ACTIVE
name: FlickrStats
projectId: flickrstats-492309
projectNumber: '781796249121'
```

---

## 3) Inspect the Cloud Function

### Command

```bash
gcloud functions list --project=flickrstats-492309 --regions=europe-west9
```

### Captured output

```text
NAME                  STATE   TRIGGER       REGION        ENVIRONMENT
flickr-daily-extract  ACTIVE  HTTP Trigger  europe-west9  2nd gen
```

### Deployment source

The repo deploys this function through [`cloudbuild.yaml`](./cloudbuild.yaml), which uses:

```bash
gcloud functions deploy flickr-daily-extract \
  --region=europe-west9 \
  --runtime=python311 \
  --trigger-http \
  --entry-point=main_handler \
  --timeout=540s \
  --memory=256MB \
  --service-account=flickr-stats-loader@flickrstats-492309.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --set-secrets=FLICKR_API_KEY=flickr-api-key:latest,FLICKR_API_SECRET=flickr-api-secret:latest,FLICKR_OAUTH_TOKEN=flickr-oauth-token:latest,FLICKR_OAUTH_TOKEN_SECRET=flickr-oauth-token-secret:latest
```

---

## 4) Inspect the backing Cloud Run service

### Command

```bash
gcloud run services list --project=flickrstats-492309 --region=europe-west9
```

### Captured output

```text
   SERVICE               REGION        URL                                                             LAST DEPLOYED BY                                              LAST DEPLOYED AT
✔  flickr-daily-extract  europe-west9  https://flickr-daily-extract-781796249121.europe-west9.run.app  service-781796249121@gcf-admin-robot.iam.gserviceaccount.com  2026-04-06T08:14:10.709863Z
!  flickrstats-git       europe-west9  https://flickrstats-git-781796249121.europe-west9.run.app       781796249121-compute@developer.gserviceaccount.com            2026-04-05T17:42:41.720037Z
```

---

## 5) Inspect Cloud Scheduler

### Command

```bash
gcloud scheduler jobs list --project=flickrstats-492309 --location=europe-west1
```

### Captured output

```text
ID                          LOCATION      SCHEDULE (TZ)             TARGET_TYPE  STATE
flickr-daily-stats-trigger  europe-west1  0 5 * * * (Europe/Paris)  HTTP         ENABLED
```

This output predates the title-cleanse job. To inspect the current schedule,
state, and most recent attempt for each job:

```bash
gcloud scheduler jobs describe flickr-daily-stats-trigger \
  --project=flickrstats-492309 \
  --location=europe-west1 \
  --format='yaml(state,schedule,timeZone,lastAttemptTime,status)'

gcloud scheduler jobs describe flickr-title-cleanse-trigger \
  --project=flickrstats-492309 \
  --location=europe-west1 \
  --format='yaml(state,schedule,timeZone,lastAttemptTime,status)'
```

`ENABLED` means the job is scheduled, not that its last invocation succeeded.
Check `lastAttemptTime` and `status`, then inspect the function logs below for
the outcome. A missing `lastAttemptTime` can indicate the job has not yet run.
`NOT_FOUND` means the named job was not found in the specified project and
location.

---

## 6) Inspect Secret Manager

### Command

```bash
gcloud secrets list --project=flickrstats-492309
```

### Captured output

```text
NAME                                    CREATED              REPLICATION_POLICY  LOCATIONS
flickr-api-key                          2026-04-04T15:32:13  automatic           -
flickr-api-secret                       2026-04-04T15:32:25  automatic           -
flickr-oauth-token                      2026-04-04T15:32:34  automatic           -
flickr-oauth-token-secret               2026-04-04T15:32:44  automatic           -
umabot-github-github-oauthtoken-57455e  2026-04-05T08:32:47  user_managed        europe-west9
```

---

## 7) Inspect service accounts and IAM

### Service accounts

```bash
gcloud iam service-accounts list \
  --project=flickrstats-492309 \
  --format='table(email,displayName,disabled)'
```

```text
EMAIL                                                           DISPLAY NAME                        DISABLED
flickr-stats-loader@flickrstats-492309.iam.gserviceaccount.com  flickr-stats-loader                 False
781796249121-compute@developer.gserviceaccount.com              Default compute service account     False
flickrstats-492309@appspot.gserviceaccount.com                  App Engine default service account  False
```

### IAM policy summary

```bash
gcloud projects get-iam-policy flickrstats-492309 \
  --flatten='bindings[].members' \
  --format='table(bindings.role,bindings.members)'
```

Key verified bindings include:

```text
roles/bigquery.dataEditor          serviceAccount:flickr-stats-loader@flickrstats-492309.iam.gserviceaccount.com
roles/bigquery.jobUser             serviceAccount:flickr-stats-loader@flickrstats-492309.iam.gserviceaccount.com
roles/secretmanager.secretAccessor serviceAccount:flickr-stats-loader@flickrstats-492309.iam.gserviceaccount.com
roles/owner                        user:silvio@innovumabot.com
```

---

## 8) Inspect BigQuery

### Dataset list

```bash
bq ls --project_id=flickrstats-492309
```

```text
   datasetId
 -------------
  flickrstats
```

### Dataset details and location

```bash
bq show --format=prettyjson flickrstats-492309:flickrstats
```

```json
{
  "datasetReference": {
    "datasetId": "flickrstats",
    "projectId": "flickrstats-492309"
  },
  "id": "flickrstats-492309:flickrstats",
  "location": "europe-west9",
  "type": "DEFAULT"
}
```

---

## 9) Useful day-2 operations

### Title cleansing deployment and operation

`cloudbuild.yaml` runs the title-selection tests, deploys the separate
`flickr-title-cleanse` function from `title_cleanse/`, grants the scheduler
service account permission to invoke it, and creates or updates the
`flickr-title-cleanse-trigger` Scheduler job. The job runs at 07:00
Europe/Paris in `europe-west1`; the function and BigQuery dataset are in
`europe-west9`. Confirm the existing daily job is still scheduled for 05:00
Europe/Paris before deploying. This is two hours after its scheduled start,
not necessarily two hours after its completion.

In addition to the existing function deployment permissions, the Cloud Build
service account needs permission to manage Cloud Scheduler jobs, grant
`roles/run.invoker` on the new Cloud Run service, and act as
`flickr-stats-loader`. The loader service account needs BigQuery job creation
and dataset read/write permissions, including permission to create the backup
table. The Scheduler service agent must be able to mint the configured OIDC
token. The Cloud Build trigger and its main-branch restriction remain
configured outside this repository.

The two-hour gap is **not a lock**. Do not manually invoke the loader or run
other writers against the target table while the cleanser is running. Ensure
the daily extraction has finished before the scheduled cleanse; if it has
not, pause the cleansing scheduler and resume it only after the load finishes.
The cleanser itself is limited to one concurrent request.

The first run with eligible changes creates
`flickrstats-492309.flickrstats.flickrstats_titles_changed`. Each successful
run appends the original full rows with `backup_run_id` and `backup_at`.
Backup and title updates commit together. Cloud logs report the run ID,
counts, and any IDs skipped because no valid dated title exists or the latest
timestamp has conflicting titles. Investigate skipped IDs separately.

To recover, identify the appropriate `backup_run_id` and restore only the
desired `Photo Title` values from that run, after stopping writers and
verifying row identity and backup contents. Do not replace the main table
with the backup: the backup contains only affected photos and may contain
multiple runs.

### Manually invoke the deployed endpoint

```bash
curl -X POST "https://flickr-daily-extract-781796249121.europe-west9.run.app" \
  -H "Authorization: bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"Date": "2026-04-01"}'
```

### Check recent function logs

The functions run in `europe-west9`, while their Scheduler jobs are in
`europe-west1`:

```bash
gcloud functions logs read flickr-daily-extract \
  --project=flickrstats-492309 \
  --region=europe-west9 \
  --gen2 \
  --limit=50

gcloud functions logs read flickr-title-cleanse \
  --project=flickrstats-492309 \
  --region=europe-west9 \
  --gen2 \
  --limit=50
```

For the extractor, look for the processed row count, successful `MERGE`, and
staging-table truncation. For the cleanser, look for the `Title cleanse`
summary with the run ID and counts; investigate warnings about skipped IDs and
any errors. Startup probes and deployment rollout messages do not establish
that a function was invoked. Timestamps in the log output are UTC.

### List enabled APIs

```bash
gcloud services list --enabled --project=flickrstats-492309
```

---

## 10) Summary

The current live setup is:

- **Project:** `flickrstats-492309`
- **Cloud Functions:** `flickr-daily-extract` and `flickr-title-cleanse` in **`europe-west9`**
- **BigQuery dataset:** `flickrstats` in **`europe-west9`**
- **Scheduler jobs:** `flickr-daily-stats-trigger` and `flickr-title-cleanse-trigger` in **`europe-west1`**
- **Execution service account:** `flickr-stats-loader@flickrstats-492309.iam.gserviceaccount.com`

This file should be the main GCP CLI reference for the project.