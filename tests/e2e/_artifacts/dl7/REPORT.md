# DL-7 DMS LINE chat QA E2E

- **G-QA1** PASS: transfer full chain — booking=BK000002608000015 search_id=49 preview_labels=True nonce=True advisor=335/sale02 attachments=['สำเนาบัตรประชาชน', 'ใบโอนเงินจอง'] payment_fields=1,500.00/1,500.00
- **G-QA2** PASS: discard preview without DMS write — receipt=True logs_before=15 logs_after=15
- **G-QA3** PASS: cash path — booking=BK000002608000016 txtmoneycash=2,000.00 attachments=['สำเนาบัตรประชาชน']
- **G-QA4** PASS: transfer requires slip — need_slip=True cash_rejected=True preview_after_image=True
- **G-QA5** PASS: mid-flow image is rejected without OCR — customer=107 reply=True ocr_delta=0
- **G-QA7** PASS: unmatched advisor blocks at start — blocked=True slip_asked=False session_state=— push_logs=0->0
- **G-QA6** PASS: nonce replay — expired=True booking_lookup_stable=True

## Booking numbers
- `BK000002608000015`
- `BK000002608000016`

## Evidence
- `dms-booking-attachments.png`
- `dms-booking-numbers.json`
- `dms-booking-payment.png`
- `outbox.json`
- `qa-preview-cash.json`
- `qa-preview-transfer.json`
- `qa1-customer-review.json`
- `qa1-dms-readback.json`
- `qa1-receipt.json`
- `qa3-dms-readback.json`
- `qa7-advisor-block.json`
- `qa7-customer-review.json`
- `results.json`
