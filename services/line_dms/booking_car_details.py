"""Show the mapped vehicle specification alongside the booking confirmation."""

from services.line_dms.cards import _kv_row

_FIELDS = (
    (4, "ยี่ห้อ"),
    (6, "ประเภทรถ"),
    (8, "รายละเอียดรถ"),
    (10, "เกรด"),
    (12, "เกียร์"),
    (13, "ปีผลิต"),
    (15, "เครื่องยนต์"),
    (16, "ราคาตาม DMS"),
)


def rows(qa):
    car_id = str(((qa.get("answers") or {}).get("car") or {}).get("id") or "")
    cars = ((qa.get("master_snapshot") or {}).get("rows") or {}).get("cars") or []
    car = next((row for row in cars if str(row[0]) == car_id), [])
    return [
        _kv_row(label, str(car[index]))
        for index, label in _FIELDS
        if len(car) > index and car[index] not in (None, "")
    ]
