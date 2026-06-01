from __future__ import annotations

import unittest

from apps.memory_gateway.app.policy import policy_summary


class MemoryGatewayPolicyTests(unittest.TestCase):
    def test_policy_summary_exposes_sdlc_contract(self) -> None:
        policy = policy_summary()

        self.assertIn("implementation_lesson", policy["allowed_memory_types"])
        self.assertEqual(policy["retrievable_status"], "approved")


if __name__ == "__main__":
    unittest.main()
