import argparse
import datetime
import time

import boto3
from colorama import Fore

REGION = ""
USER_POOL_ID = ""
LIMIT = 60
MAX_NUMBER_RECORDS = 0
REQUIRED_ATTRIBUTE = []
CSV_FILE_NAME = "CognitoUsers.csv"

""" Parse All Provided Arguments """
parser = argparse.ArgumentParser(
    description="Cognito User Pool export records to CSV file",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    "-attr",
    "--export-attributes",
    nargs="+",
    type=str,
    help="List of Attributes to be saved in CSV",
    required=True,
)
parser.add_argument("--user-pool-id", type=str, help="The user pool ID", required=True)
parser.add_argument(
    "--region", type=str, default="us-east-1", help="The user pool region"
)
parser.add_argument("-f", "--file-name", type=str, help="CSV File name")
parser.add_argument(
    "--num-records", type=int, help="Max Number of Cognito Records to be exported"
)
args = parser.parse_args()

if args.export_attributes:
    REQUIRED_ATTRIBUTE = list(args.export_attributes)
if args.user_pool_id:
    USER_POOL_ID = args.user_pool_id
if args.region:
    REGION = args.region
if args.file_name:
    CSV_FILE_NAME = args.file_name
if args.num_records:
    MAX_NUMBER_RECORDS = args.num_records


def datetimeconverter(o):
    if isinstance(o, datetime.datetime):
        return str(o)


def get_list_cognito_users(cognito_idp_cliend, next_pagination_token="", Limit=LIMIT):

    return (
        client.list_users(
            UserPoolId=USER_POOL_ID,
            Limit=Limit,
            PaginationToken=next_pagination_token,
        )
        if next_pagination_token
        else client.list_users(
            UserPoolId=USER_POOL_ID,
            Limit=Limit,
        )
    )


""" TODO: Write to file function helper for all Cognito Pool atrributes
def write_cognito_records_to_file(file_name: str, cognito_records: list) -> bool:
    try:
        csv_file = open(file_name, 'a')
        cognito_records.insert(0, ",".join(REQUIRED_ATTRIBUTE))
        csv_file.writelines(cognito_records)
        csv_file.close()
        return True
    except:
        print("Something went wrong while writing to file") 
"""

client = boto3.client("cognito-idp", REGION)
csv_new_line = {REQUIRED_ATTRIBUTE[i]: "" for i in range(len(REQUIRED_ATTRIBUTE))}
try:
    csv_file = open(CSV_FILE_NAME, "w")
    csv_file.write(",".join(csv_new_line.keys()) + "\n")
except Exception as err:
    error_message = repr(err)  
    print(Fore.RED + "\nERROR: Can not create file: " + CSV_FILE_NAME)
    print("\tError Reason: " + error_message)
    exit()

pagination_counter = 0
exported_records_counter = 0
pagination_token = ""
while pagination_token is not None:
    csv_lines = []
    try:
        user_records = get_list_cognito_users(
            cognito_idp_cliend=client,
            next_pagination_token=pagination_token,
            Limit=LIMIT if LIMIT < MAX_NUMBER_RECORDS else MAX_NUMBER_RECORDS,
        )
    except client.exceptions.ClientError as err:
        error_message = err.response["Error"]["Message"]
        print(Fore.RED + "Please Check your Cognito User Pool configs")
        print("Error Reason: " + error_message)
        csv_file.close()
        exit()
    except:
        print(Fore.RED + "Something else went wrong")
        csv_file.close()
        exit()


    """ Check if there next paginatioon is exist """
    if set(["PaginationToken", "NextToken"]).intersection(set(user_records)):
        pagination_token = (
            user_records["PaginationToken"]
            if "PaginationToken" in user_records
            else user_records["NextToken"]
        )
    else:
        pagination_token = None

    for user in user_records["Users"]:
        """Fetch Required Attributes Provided"""
        csv_line = csv_new_line.copy()
        for requ_attr in REQUIRED_ATTRIBUTE:
            csv_line[requ_attr] = ""
            if requ_attr in user.keys():
                csv_line[requ_attr] = str(user[requ_attr])
                continue
            for usr_attr in user["Attributes"]:
                if usr_attr["Name"] == requ_attr:
                    csv_line[requ_attr] = str(usr_attr["Value"])

        csv_lines.append(",".join(csv_line.values()) + "\n")

    csv_file.writelines(csv_lines)

    """ Display Proccess Infor """
    pagination_counter += 1
    exported_records_counter += len(csv_lines)
    print(
        Fore.YELLOW
        + "Page: #{} \n Total Exported Records: #{} \n".format(
            str(pagination_counter), str(exported_records_counter)
        )
    )

    if MAX_NUMBER_RECORDS and exported_records_counter >= MAX_NUMBER_RECORDS:
        print(Fore.GREEN + "INFO: Max Number of Exported Reached")
        break

    if pagination_token is None:
        print(Fore.GREEN + "INFO: End of Cognito User Pool reached")

    """ Cool Down before next batch of Cognito Users """
    time.sleep(0.15)

""" Close File """
csv_file.close()
