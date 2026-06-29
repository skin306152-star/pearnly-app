# -*- coding: utf-8 -*-
"""缺口④ · 网页 OCR 上传异步队列(ocr_jobs)。

提交即返 job_id,后台 worker 跑 pipeline→persist→push→charge,前端轮询拿进度+结果。
镜像 services/recon_jobs 的 Postgres-as-queue 范式(FOR UPDATE SKIP LOCKED + 租约),
但带 OCR 专属:result(同形 recognize JSON)+ charged_at(扣费幂等,防重试重扣)。
"""
