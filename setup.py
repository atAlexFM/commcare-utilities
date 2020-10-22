from setuptools import setup

setup(
    name="commcare_utilities",
    version="0.1",
    description="Helpful utilities for working with CommCare",
    url="https://github.com/caktus/commcare-utilities",
    author="Benjamin White",
    author_email="ben@benjamineugenewhite.com",
    # license="MIT",   if/when we open source this, need to set right license type
    packages=["cc_utilities", "cc_utilities.command_line"],
    install_requires=[
        "commcare-export",
        "retry",
        "dateparser",
        "openpyxl",
        "requests",
        "SQLAlchemy",
        "phonenumbers",
        "pandas",
        "numpy",
        "xlrd",
    ],  # adding comment here because otherwise conflict b/w Flake8 and black in precommit hooks
    entry_points={
        "console_scripts": [
            "process-numbers-for-sms-capability=cc_utilities.command_line.process_numbers_for_sms_capability:main",
            "generate-case-export-query-file=cc_utilities.command_line.generate_case_export_query_file:main",
            "bulk-upload-legacy-contact-data=cc_utilities.command_line.bulk_upload_legacy_contact_data:main",
            "sync-commcare-case-type-to-db=cc_utilities.command_line.sync_commcare_case_type_to_db:main",
        ]
    },
    zip_safe=False,
)
