# Setting Up the Automated Stock-Threshold Engine

This document explains how to set up the Automated Stock-Threshold Engine which, according to the PRD (Section 3.3), needs to run every 15 minutes to evaluate inventory thresholds.

## Overview

The Automated Stock-Threshold Engine implements this formula from the PRD:
```
reorder_point = safety_stock + (avg_daily_sales × lead_time_days)
```

And sets alert levels based on:
- RED if on_hand ≤ reorder_point
- YELLOW if on_hand ≤ reorder_point + safety_stock

## Implementation Options

There are three ways to set up the recurring 15-minute task:

1. Using cron-job.org (recommended for simplicity)
2. Using GitHub Actions (included in this repo)
3. Using AWS Lambda with EventBridge (as mentioned in the PRD)

This document focuses on the first two options, which are easier to set up without AWS infrastructure.

## Option 1: Using cron-job.org

There are two ways to authenticate with the cron endpoint: using a time-based signature or using a simple API key.

### Method A: Using a Static API Key (Simpler)

#### Step 1: Set Environment Variables

Ensure your API server has the `CRON_API_KEY` environment variable set to a secure random string.

```bash
# Add to your .env file
CRON_API_KEY=your-secure-random-string
```

#### Step 2: Set Up the Cron Job at cron-job.org

1. Sign up at [cron-job.org](https://cron-job.org)
2. Create a new cronjob:
   - Title: `Steadi - Threshold Evaluator`
   - URL: `https://your-api-domain/cron/threshold-evaluator-simple`
   - Request method: `POST`
   - Authentication: None
   - Custom HTTP Headers:
     - `X-API-Key`: [The value you set for CRON_API_KEY]
   - Schedule: Every 15 minutes
   - Execution timeout: 60 seconds

3. Save the cronjob

### Method B: Using a Time-Based Signature (More Secure)

#### Step 1: Set Environment Variables

Ensure your API server has the `CRON_SECRET_KEY` environment variable set to a secure random string.

```bash
# Add to your .env file
CRON_SECRET_KEY=your-secure-random-string
```

#### Step 2: Generate a Signature

Run the provided utility script to generate a signature:

```bash
cd app/scripts
python generate_cron_signature.py
```

This will output instructions and a signature you'll need for the next step.

#### Step 3: Set Up the Cron Job at cron-job.org

1. Sign up at [cron-job.org](https://cron-job.org)
2. Create a new cronjob:
   - Title: `Steadi - Threshold Evaluator`
   - URL: `https://your-api-domain/cron/threshold-evaluator`
   - Request method: `POST`
   - Authentication: None
   - Custom HTTP Headers:
     - `X-Cron-Signature`: [Use the signature generated in step 2]
   - Schedule: Every 15 minutes
   - Execution timeout: 60 seconds

3. Save the cronjob

Note: The signature will expire in ~2 minutes, so set up the cronjob quickly after generating it.

## Option 2: Using GitHub Actions

This repository includes a GitHub Actions workflow that triggers the threshold evaluator every 15 minutes.

### Step 1: Configure GitHub Secrets

You need to add two secrets to your GitHub repository:

1. Choose either:
   - `CRON_SECRET_KEY`: For the time-based signature authentication
   - `CRON_API_KEY`: For the simpler API key authentication
2. `API_BASE_URL`: The base URL of your API (e.g., `https://api.steadi.app`)

To add secrets:
1. Navigate to your GitHub repository
2. Click Settings → Secrets → Actions
3. Click "New repository secret"
4. Add the secrets mentioned above

### Step 2: Enable the GitHub Actions Workflow

The workflow file is located at `.github/workflows/threshold-evaluator.yml`. The workflow will run automatically every 15 minutes, but you can also trigger it manually:

1. Go to the Actions tab in your GitHub repository
2. Select "Threshold Evaluator Cron" from the list of workflows
3. Click "Run workflow" to test it

## Option 3: AWS Lambda (Future Implementation)

For a more scalable approach, consider implementing an AWS Lambda function with EventBridge as specified in the PRD. This approach would involve:

1. Creating a Lambda function that calls your ThresholdService logic
2. Setting up an EventBridge rule with a rate of 15 minutes
3. Setting the Lambda as the target for the EventBridge rule

## Testing the Endpoints

### Testing the API Key Endpoint

```bash
curl -X POST https://your-api-domain/cron/threshold-evaluator-simple \
  -H 'X-API-Key: your-api-key'
```

### Testing the Signature-Based Endpoint

```bash
# First, generate a signature
cd app/scripts
python generate_cron_signature.py

# Use the generated signature in the curl request
curl -X POST https://your-api-domain/cron/threshold-evaluator \
  -H 'X-Cron-Signature: your-generated-signature'
```

## Monitoring

Regardless of which method you choose, you should monitor the execution of the threshold evaluator:

1. Check the logs of your FastAPI server
2. Set up alerts for failed executions
3. Periodically verify that inventory thresholds are being calculated correctly

## Troubleshooting

If the threshold evaluator is not working as expected:

1. Verify that the correct authentication is being sent
2. Check the FastAPI server logs for any error messages
3. Ensure the database connection is working properly
4. Verify that the ThresholdService is calculating values correctly
5. Test the endpoint manually to see if it returns a valid response 