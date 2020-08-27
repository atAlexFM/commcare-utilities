import argparse
import sys

import phonenumbers
import requests
from sqlalchemy import create_engine

from common import upload_data_to_commcare

TWILIO_LOOKUP_URL = "https://lookups.twilio.com/v1/PhoneNumbers"
# NB update this when we hear back what is possible here
COMMCARE_CAN_RECIEVE_SMS_FIELD_NAME = "can_receive_sms"


def format_phone_number(raw, region="US"):
    parsed = phonenumbers.parse(raw, region=region)
    return f"+{parsed.country_code}{parsed.national_number}"


def twilio_lookup_phone_number(number, sid, auth_token):
    response = requests.get(
        f"{TWILIO_LOOKUP_URL}/{number}",
        auth=(sid, auth_token),
        params={"Type": "carrier"},
    )
    return response.json()["carrier"]["type"]


def can_receive_sms(number_type):
    return number_type == "mobile"


def process_phone_number(formatted_number, sid, auth_token):
    return can_receive_sms(
        twilio_lookup_phone_number(formatted_number, sid, auth_token)
    )


def get_unprocessed_contact_phone_numbers(db_url, search_column):
    """
    """
    engine = create_engine(db_url)
    # temporarily have `AND TRUE` as placeholder for whatever field will contain
    # SMSable info. We'll want to filter out rows that have this value empty/null
    # and refer to that property by string substituting
    # COMMCARE_CAN_RECIEVE_SMS_FIELD_NAME defined at top of file
    query = f"""
        SELECT {search_column}, contact_phone_number FROM contact
        WHERE
            contact_phone_number IS NOT NULL
            AND LENGTH(contact_phone_number) > 0
            AND TRUE
    """
    conn = engine.connect()
    try:
        result = conn.execute(query)
        return [dict(row) for row in result.fetchall()]
    finally:
        conn.close()


def main(
    db_url,
    commcare_user_name,
    commcare_api_key,
    commcare_project_name,
    twilio_sid,
    twilio_token,
    search_column,
):
    exit_status = 0
    data = [
        dict(item, **{COMMCARE_CAN_RECIEVE_SMS_FIELD_NAME: None})
        for item in get_unprocessed_contact_phone_numbers(db_url, search_column)
    ]
    _data = []
    for item in data:
        try:
            item["contact_phone_number"] = format_phone_number(
                item["contact_phone_number"]
            )
            _data.append(item)
        except phonenumbers.NumberParseException:
            print(
                f"The number \"{item['contact_phone_number']}\" for contcact "
                f"'{item[search_column]}' cannot be parsed and will not be further "
                f"processed."
            )
    data = _data

    processed_count = 0
    try:
        for idx, item in enumerate(data):
            data[idx]["can_receive_sms"] = process_phone_number(
                item["contact_phone_number"], twilio_sid, twilio_token,
            )
            processed_count += 1
    except Exception as exc:
        exit_status = 1
        print(f"Something went wrong: {exc}")
        if processed_count > 0:
            print(
                f"Will attempt to upload the {processed_count} numbers successfully "
                f"processed so far to CommCare"
            )
    finally:
        processed = [item for item in data if item["can_receive_sms"] is not None]
        for item in processed:
            del item["contact_phone_number"]
        if processed:
            upload_data_to_commcare(
                processed,
                commcare_project_name,
                "contact",
                search_column,
                commcare_user_name,
                commcare_api_key,
                "off",
            )
    sys.exit(exit_status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--db",
        help="The db url string of the db that contains contact data",
        dest="db_url",
    )
    parser.add_argument(
        "--username",
        help="The Commcare username (email address)",
        dest="commcare_user_name",
    )
    parser.add_argument("--apikey", help="A Commcare API key", dest="commcare_api_key")
    parser.add_argument(
        "--project", help="The Commcare project name", dest="commcare_project_name"
    )
    parser.add_argument(
        "--twilioSID", help="The SID of a Twilio account", dest="twilio_sid"
    )
    parser.add_argument(
        "--twilioToken", help="Auth token for the Twilio account", dest="twilio_token"
    )
    parser.add_argument(
        "--searchColumn",
        help="The column in db that will be matched as ID against Commcare's ID",
        dest="search_column",
        default="id",
    )
    args = parser.parse_args()
    main(
        args.db_url,
        args.commcare_user_name,
        args.commcare_api_key,
        args.commcare_project_name,
        args.twilio_sid,
        args.twilio_token,
        args.search_column,
    )
