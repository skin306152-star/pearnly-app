"""Print a budget request only; never create or update a billing budget."""

import argparse
from decimal import Decimal
import json

# Cloud Billing Catalog API live read, 2026-09-05. Reverify when changing scope.
SERVICES = {
    "Cloud Run": "services/152E-C115-5142",
    "Cloud Storage": "services/95FF-2EF5-5EA1",
    "Artifact Registry": "services/149C-F9EC-3994",
    "Cloud Tasks": "services/F3A6-D7B7-9BDA",
    "Cloud Scheduler": "services/1F14-4801-0E16",
    "Secret Manager": "services/EE82-7A5E-871C",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--amount", required=True, type=Decimal)
    parser.add_argument("--currency", required=True)
    parser.add_argument("--include-supporting-services", action="store_true")
    args = parser.parse_args()
    if (
        not args.amount.is_finite()
        or args.amount <= 0
        or not args.currency.isalpha()
        or len(args.currency) != 3
    ):
        parser.error("positive amount and billing-account currency code required")
    units = int(args.amount)
    services = (
        SERVICES
        if args.include_supporting_services
        else {key: SERVICES[key] for key in ("Cloud Run", "Cloud Storage")}
    )
    print(
        json.dumps(
            {
                "displayName": "Pearnly Cloud Run infrastructure",
                "budgetFilter": {
                    "projects": ["projects/112074003592"],
                    "services": list(services.values()),
                    "calendarPeriod": "MONTH",
                    "creditTypesTreatment": "INCLUDE_ALL_CREDITS",
                },
                "amount": {
                    "specifiedAmount": {
                        "currencyCode": args.currency.upper(),
                        "units": str(units),
                        "nanos": int((args.amount - units) * 1_000_000_000),
                    }
                },
                "thresholdRules": [
                    {"thresholdPercent": fraction, "spendBasis": "CURRENT_SPEND"}
                    for fraction in (0.5, 0.9, 1.0)
                ]
                + [{"thresholdPercent": 1.0, "spendBasis": "FORECASTED_SPEND"}],
                "notificationsRule": {"disableDefaultIamRecipients": True},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
