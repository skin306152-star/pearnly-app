"""E2E: 给 pearnly_e2e_3 造一条 Express direction_unknown(主体没绑)异常 → 验绑主体面板。
幂等:先删本账号的 Express 测试端点 + 其 push log,再建。只动该测试账号。
"""

import uuid
from core import db

U = "4d4b13b9-c254-4399-a4e0-845d67812f05"
T = "152de6e5-29eb-437d-bb2c-5d408695e60e"


def main():
    with db.get_cursor(commit=True) as cur:
        # 清旧 Express 测试端点 + 其日志(幂等)
        cur.execute("SELECT id FROM erp_endpoints WHERE user_id=%s AND adapter='express'", (U,))
        old = [r["id"] for r in cur.fetchall()]
        for eid in old:
            cur.execute("DELETE FROM erp_push_logs WHERE endpoint_id=%s", (eid,))
        cur.execute("DELETE FROM erp_endpoints WHERE user_id=%s AND adapter='express'", (U,))

        ep = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO erp_endpoints
               (id,user_id,name,adapter,config,is_default,auto_push,enabled,success_count,failure_count,tenant_id)
               VALUES (%s,%s,'Express 测试',%s,%s::jsonb,false,false,true,0,0,%s)""",
            (ep, U, "express", '{"account_set":"DATAT"}', T),
        )

        # 取一条 history 挂异常
        cur.execute(
            "SELECT id,invoice_no,seller_name,total_amount FROM ocr_history WHERE user_id=%s ORDER BY created_at DESC LIMIT 1",
            (U,),
        )
        h = cur.fetchone()

        cur.execute(
            """INSERT INTO erp_push_logs
               (id,user_id,endpoint_id,history_id,invoice_no,seller_name,total_amount,
                status,http_status,request_body,response_body,error_msg,attempt,elapsed_ms,
                trigger,tenant_id,retry_count,max_retries,next_retry_at,created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,'manual',NULL,
                       %s::jsonb,NULL,%s,1,420,'manual',%s,0,3,NULL,NOW())""",
            (
                str(uuid.uuid4()),
                U,
                ep,
                h["id"],
                h["invoice_no"],
                h["seller_name"],
                h["total_amount"],
                '{"adapter":"express","history_id":"%s"}' % h["id"],
                "EXPRESS_MANUAL: direction_unknown",
                T,
            ),
        )

        cur.execute("SELECT status, error_msg FROM erp_push_logs WHERE endpoint_id=%s", (ep,))
        print("seeded express endpoint:", ep)
        print("logs:", [dict(r) for r in cur.fetchall()])
        print("on history:", h["invoice_no"], h["id"])


if __name__ == "__main__":
    main()
