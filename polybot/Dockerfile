FROM python:3.10-alpine

# Set the working directory
WORKDIR /usr/src/app

# Copy requirements.txt and install dependencies
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip cache purge
RUN pip install -r requirements.txt
RUN pip install --no-cache-dir matplotlib

# Copy the rest of the application files
COPY . .

#ENV CERTIFICATE_ARN=""
#ENV TELEGRAM_SECRET_TOKEN=""
#ENV S3_BUCKET="dsarid-aws-project-s3"
#ENV TELEGRAM_APP_URL="danielms-lb-1875524174.eu-central-1.elb.amazonaws.com:8443"
#ENV DYNAMO_NAME="danielms-aws-project-ddb"
#ENV SQS_QUEUE_NAME="dms-aws-project-queue"

# Specify the command to run the application
CMD ["python3", "app.py"]
