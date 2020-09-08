# commcare-utilities

<!-- markdownlint-disable no-inline-html -->
<p align="left">
  <a href="https://github.com/caktus/commcare-utilities/actions?query=workflow%3A%22Test%22"><img alt="test status badge" src="https://github.com/caktus/commcare-utilities/workflows/Test/badge.svg"></a>
</p>
<!-- markdownlint-enable no-inline-html -->

This repo is for an assortment of scripts for developers working with Commcare.

## Setup

1. Create and source a virtual environment.
2. `pip3 install -e .`
3. Check if there are additional dependencies required for any of the scripts you wish to run (see below), and install them.
4. Enjoy.

## Tests

To run tests, from root of repo, do:

```bash
tox
```

## Scripts

### `generate-case-export-query-file`

This script allows a user to generate an Excel query file to facilitate exporting data from CommCare to a SQL database or other local data store. It does by iterating over all records returned in the supplied [Case Summary](https://confluence.dimagi.com/display/commcarepublic/App+Summary#AppSummary-CaseSummary) Excel file to build a list of all observed property names to be turned into column names in a SQL db.

An Excel workbook is created [as required by `commcare-export`](https://confluence.dimagi.com/display/commcarepublic/CommCare+Data+Export+Tool#CommCareDataExportTool-HowtoGenerateanExcelQueryFile), containing source to target column mappings. A separate tab is created for each case type. This same information is stored in a JSON, to make results auditable without requiring Excel. The JSON files are for informational purposes only; they can, for example, be checked into version control in a separate repository to help identify and provide a log of changes to the columns in the database over time. The JSON files are not used as an input to the process, so it is possible for fields to be removed if they are deprecated in the CommCare app.

Note the following oddity: When `commcare-export` encounters properties that do not have >=1 non-empty value in the source data, it will not add a column for that property type to the database. If on subsequent runs at least one case has been added with a non-null for the property, the property will be added as a column. This behavior was observed in a Postgres db; other flavors of SQL were not tested. This means that the source-to-target mappings that are indicated in the JSON and Excel files are not a record of what was actually synced to the db, only what was attempted.

**Running the script:**

1. Navigate to the [Case Summary](https://confluence.dimagi.com/display/commcarepublic/App+Summary#AppSummary-CaseSummary) page (under App Summary) in the CommCare web interface, and download the corresponding Excel file. It should have an "All Case Properties" tab (this is the only tab that is needed).
2. Run the script, specifying the input file, desired case type(s), and output locations. For instance, to export "patient" and "contact" case records:

    CASE_SUMMARY_FILE="MyApp - All Case Properties.xlsx"
    STATE_DIR="repo/export_query_files/commcare-project-name/"
    OUTPUT_FILE="${STATE_DIR}query_file.xlsx"

    generate-case-export-query-file --case-summary-file "$CASE_SUMMARY_FILE" --case-type patient contact --state-dir $STATE_DIR --output $OUTPUT_FILE

3. Run the `commcare-export` tool as provided in [its documentation](https://confluence.dimagi.com/display/commcarepublic/CommCare+Data+Export+Tool). Any new columns added to the DB will be noted in the command-line output of the script.

### `batch-process-contacts-for-can-receive-sms`

This script allows a user to run unprocessed contact phone numbers through the [Twilio Lookup API](https://www.twilio.com/docs/lookup/api) in order to determine if contacts can be reached by SMS. To do this, it queries a database for unprocessed contacts, queries the Twilio Lookup API for each number, then uses the [CommCare bulk upload API](https://confluence.dimagi.com/display/commcarepublic/Bulk+Upload+Case+Data) to update the `contact_phone_can_receive_sms` property on these cases.

Note that this script does not update the database it originally queries.

Also note that when this script encounters numbers that either a.) cannot be parsed to generate the standard format required by Twilio, or b.) are not found to be a valid number by the Twilio API, the script marks these numbers as not capable of receiving SMS, and logs a warning to a log file.

Finally, note that this script presently is configured to work with US-based phone numbers and any non-US numbers it encounters will marked as not able to receive SMS.

**Running the script:**

1. Create a Twilio account if you don't already have one.
2. Gather your Twilio SID and auth token.
3. Install the appropriate db engine library for your database. If you're not sure what that is, run the script without doing this, and you'll get a `ModuleNotFoundError` with the name of the required library.
4. Optionally, copy over `sample.env` to `.env` and insert appropriate values. Source those values before the next step.
5. Run the script. Assuming the referenced variables are set: `batch-process-contacts-for-can-receive-sms --db $DB_URL --username $COMMCARE_USER --apikey $COMMCARE_API_KEY --project $COMMCARE_PROJECT --twilioSID $TWILIO_SID --twilioToken $TWILIO_TOKEN`.
6. Any new columns added to the DB will be noted in the command-line output of the script.

## Logging

By default, this package logs to a .gitignored log file at `logs/cc-utilities.log`. This file is limited to 5MB and beyond that size, the log will be rotated. To log to a non-default location, you can set an env var for `COMMCARE_UTILITIES_LOG_PATH` for a directory in which to save logs.
