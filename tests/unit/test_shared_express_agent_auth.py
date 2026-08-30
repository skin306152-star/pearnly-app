import hashlib
import unittest
from dataclasses import FrozenInstanceError
from uuid import UUID

from services.erp import shared_express_agent_auth as auth
from services.erp.express_push.agent_store import hash_token

TOKEN = "exp_123e4567-e89b-12d3-a456-426614174000_secret-abc"
TOKEN_WITH_URLSAFE_SEPARATORS = "exp_123e4567-e89b-12d3-a456-426614174000_a_b-_c_"


class ManagedAgentAuthTests(unittest.TestCase):
    def test_companion_token_returns_canonical_id_and_digest(self):
        parsed = auth.parse_managed_agent_token(TOKEN)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.endpoint_id, str(UUID(parsed.endpoint_id)))
        self.assertEqual(parsed.token_digest, hashlib.sha256(TOKEN.encode()).hexdigest())

    def test_digest_matches_existing_agent_store_hash(self):
        parsed = auth.parse_managed_agent_token(TOKEN)
        self.assertEqual(parsed.token_digest, hash_token(TOKEN))
        self.assertTrue(auth.stored_token_matches(hash_token(TOKEN), parsed.token_digest))
        self.assertFalse(auth.stored_token_matches("0" * 64, parsed.token_digest))

    def test_existing_urlsafe_secret_separators_remain_compatible(self):
        parsed = auth.parse_managed_agent_token(TOKEN_WITH_URLSAFE_SEPARATORS)
        self.assertIsNotNone(parsed)
        self.assertTrue(
            auth.stored_token_matches(
                hash_token(TOKEN_WITH_URLSAFE_SEPARATORS), parsed.token_digest
            )
        )

    def test_result_is_immutable_and_has_no_plaintext(self):
        parsed = auth.parse_managed_agent_token(TOKEN)
        self.assertNotIn("secret-abc", repr(parsed))
        with self.assertRaises(FrozenInstanceError):
            parsed.endpoint_id = "x"

    def test_rejects_empty_malformed_or_ambiguous_tokens(self):
        endpoint = "123e4567-e89b-12d3-a456-426614174000"
        invalid = (
            "",
            " ",
            "exp_",
            f"exp_{endpoint}",
            f"exp_{endpoint}_",
            "exp_123e4567e89b12d3a456426614174000_secret",
            f"exp__{endpoint}_secret",
            f"exp_{endpoint}_ secret",
            f"exp_{endpoint}_secret\n",
        )
        for token in invalid:
            with self.subTest(token=token):
                self.assertIsNone(auth.parse_managed_agent_token(token))

    def test_uuid_case_normalizes_but_digest_stays_bound_to_original_token(self):
        token = f"exp_{'123e4567-e89b-12d3-a456-426614174000'.upper()}_secret"
        parsed = auth.parse_managed_agent_token(token)
        self.assertEqual(parsed.endpoint_id, "123e4567-e89b-12d3-a456-426614174000")
        self.assertFalse(auth.stored_token_matches(hash_token(TOKEN), parsed.token_digest))

    def test_rejects_non_string_and_oversized_tokens(self):
        self.assertIsNone(auth.parse_managed_agent_token(None))
        self.assertIsNone(auth.parse_managed_agent_token("exp_" + "a" * 1025))

    def test_digest_comparison_rejects_malformed_values(self):
        digest = hashlib.sha256(TOKEN.encode()).hexdigest()
        self.assertTrue(auth.stored_token_matches(digest, digest))
        self.assertFalse(auth.stored_token_matches(digest.upper(), digest))
        self.assertFalse(auth.stored_token_matches("short", digest))
        self.assertFalse(auth.stored_token_matches(digest, b"x" * 64))


if __name__ == "__main__":
    unittest.main()
