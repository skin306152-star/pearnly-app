# MR.ERP DMS Recovery Contract

## Confirmed Failure Chain

The DMS test account `dmstest` permits only one active login. A desktop DMS
session and a LINE booking session using the same credentials can trigger the
DMS alert for duplicate login, after which one session is forcibly logged out.
Pearnly must classify that alert as `ERR_DMS_CONCURRENT_LOGIN`, not as a
generic network timeout.

The booking editor previously served the endpoint's 12-hour master cache. A
production read-only probe returned two vehicle rows and two company-bank
rows, while the cached snapshot still contained one bank row. The editor now
forces one master refresh when a pending booking is opened and obtains customer
prefixes in that same authenticated DMS session.

## Recovery Contract

- Duplicate-login and pre-create company-bank readiness failures preserve the
  complete `booking_review` payload.
- The failure response contains a LINE Flex retry card with a one-time nonce.
- The retry state expires after 30 minutes and creates a fresh DMS session.
- Errors after an uncertain booking write never receive an automatic retry
  card, preventing duplicate bookings.
- Successful retry clears the booking session and returns the normal booking
  receipt.

## Verification

The LINE simulation covers confirm → duplicate-login failure → retry postback →
successful booking. The editor contract asserts a forced master refresh and
the existing browser test covers the mobile booking editor layout.
