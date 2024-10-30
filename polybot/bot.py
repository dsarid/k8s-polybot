import telebot
from loguru import logger
import os
import time
from datetime import datetime
from telebot.types import InputFile
import polybot_helper_lib
import boto3
import json


class Bot:

    def __init__(self, token, telegram_chat_url, cert, region):
        # create a new instance of the TeleBot class.
        # all communication with Telegram servers are done using self.telegram_bot_client
        self.telegram_bot_client = telebot.TeleBot(token)

        # remove any existing webhooks configured in Telegram servers
        self.telegram_bot_client.remove_webhook()
        time.sleep(0.5)

        # set the webhook URL
        boto_client = boto3.client('acm', region_name=region)
        self.telegram_bot_client.set_webhook(
            url=f'{telegram_chat_url}/{token}/',
            timeout=60,
            certificate=boto_client.get_certificate(CertificateArn=cert)["Certificate"]
        )

        logger.info(f'Telegram Bot information\n\n{self.telegram_bot_client.get_me()}')

    def send_text(self, chat_id, text):
        self.telegram_bot_client.send_message(chat_id, text)

    def send_text_with_quote(self, chat_id, text, quoted_msg_id):
        self.telegram_bot_client.send_message(chat_id, text, reply_to_message_id=quoted_msg_id)

    @staticmethod
    def is_current_msg_photo(msg):
        return 'photo' in msg

    def download_user_photo(self, msg):
        """
        Downloads the photos that sent to the Bot to `photos` directory (should be existed)
        :return:
        """
        if not self.is_current_msg_photo(msg):
            raise RuntimeError(f'Message content of type \'photo\' expected')

        file_info = self.telegram_bot_client.get_file(msg['photo'][-1]['file_id'])
        data = self.telegram_bot_client.download_file(file_info.file_path)
        folder_name = file_info.file_path.split('/')[0]

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        with open(file_info.file_path, 'wb') as photo:
            photo.write(data)

        return file_info.file_path

    def send_photo(self, chat_id, img_path):
        if not os.path.exists(img_path):
            raise RuntimeError("Image path doesn't exist")

        self.telegram_bot_client.send_photo(
            chat_id,
            InputFile(img_path)
        )

    def handle_message(self, msg):
        """Bot Main message handler"""
        logger.info(f'Incoming message: {msg}')
        self.send_text(msg['chat']['id'], f'Your original message: {msg["text"]}')


class ObjectDetectionBot(Bot):
    def __init__(self, token, telegram_chat_url, cert, images_bucket, region):
        super().__init__(token, telegram_chat_url, cert, region)
        self.media_group = None
        self.filter = None

        self.queue_name = os.environ["SQS_QUEUE_NAME"]
        self.sqs_client = boto3.client('sqs', region_name=region)
        self.s3 = boto3.client('s3')

        self.previous_pic = None
        self.images_bucket = images_bucket

    @staticmethod
    def _add_date_to_filename_(file_path):
        """added a date to a given filename"""
        # Split the file path into directory and filename
        directory, filename = os.path.split(file_path)

        # Get the current date
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Extract file extension
        name, extension = os.path.splitext(filename)

        # Create the new filename with the date appended
        new_filename = f"{name}_{current_date}{extension}"

        # Construct the new file path
        new_file_path = os.path.join(directory, new_filename)

        try:
            # Rename the file
            os.rename(file_path, new_file_path)
            print(f"File renamed to: {new_filename}")
            return new_file_path
        except Exception as e:
            print(f"Error: {e}")
        return None

    def handle_message(self, msg):
        logger.info(f'Incoming message: {msg}')

        if self.is_current_msg_photo(msg):
            photo_path = self.download_user_photo(msg)

            # Upload the photo to S3
            message_received = False
            if msg.get("caption") == "Predict":
                self.filter = msg.get("caption")

                logger.info("\nFilter set to Predict\n")

            if self.filter.lower() == "predict":
                photo_path = self.download_user_photo(msg)

                logger.info(f"\nDownload image: {self.images_bucket}\n")

                photo_path = self._add_date_to_filename_(photo_path)

                logger.info("\nadded path\n")

                polybot_helper_lib.upload_file(photo_path, self.images_bucket, self.s3)

                # Delete the received image after uploading it to s3
                if os.path.exists(photo_path):
                    os.remove(photo_path)
                else:
                    print("The file does not exist")

                logger.info("\nUploaded file to s3\n")

                s3_img_name = os.path.split(photo_path)

                # check up to 5 times if the file is in the s3 bucket
                for i in range(5):
                    try:
                        logger.info(f"File name: {s3_img_name[1]}")
                        self.s3.head_object(
                            Bucket=self.images_bucket,
                            Key=s3_img_name[1]
                        )
                        message_received = True
                        break
                    except Exception as E:
                        logger.info(f"file probably not there yet :/ attempt no: {i}")
                        time.sleep(5)

                if not message_received:
                    self.send_text(msg['chat']['id'], text="Internal server error, please try again later")
                    self.filter = None

                else:
                    # Send a job to the SQS queue
                    message_dict = {
                        "img_name": s3_img_name[1],
                        "msg_id": msg['chat']['id']
                    }

                    # send message to the Telegram end-user (e.g. Your image is being processed. Please wait...)
                    json_string = json.dumps(message_dict, indent=4)
                    response = self.sqs_client.send_message(QueueUrl=self.queue_name, MessageBody=json_string)
                    print(response)
                    self.send_text(msg['chat']['id'], text="Your image is being processed. Please wait...")

            else:
                self.send_text(msg['chat']['id'], "Please send a picture with \"Predict\" comment.")
                self.filter = None

        else:
            self.send_text(msg['chat']['id'], "Please send a picture with \"Predict\" comment.")
            self.filter = None
