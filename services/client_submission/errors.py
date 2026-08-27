"""Client submission 稳定错误码。"""


class SubmissionError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


REVISION_CONFLICT = "ERR_SUBMISSION_REVISION_CONFLICT"
DELIVERY_FAILED = "ERR_SUBMISSION_DELIVERY"
TARGET_MISMATCH = "ERR_ENGAGEMENT_WORKSPACE_MISMATCH"
ENGAGEMENT_NOT_ACTIVE = "ERR_ENGAGEMENT_NOT_ACTIVE"

PUBLIC_CODES = frozenset(
    {
        REVISION_CONFLICT,
        DELIVERY_FAILED,
        TARGET_MISMATCH,
        ENGAGEMENT_NOT_ACTIVE,
    }
)
