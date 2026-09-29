import unittest
from tonelli_shanks import tonelli_shanks


class TestTonelliShanks(unittest.TestCase):

    def test_trivial_and_edge_cases(self):
        """Test zero residues and the special prime p=2."""
        self.assertEqual(tonelli_shanks(0, 7), 0)
        self.assertEqual(tonelli_shanks(7, 7), 0)

        # p = 2
        self.assertEqual(tonelli_shanks(0, 2), 0)
        self.assertEqual(tonelli_shanks(1, 2), 1)
        self.assertEqual(tonelli_shanks(3, 2), 1)  # 3 % 2 == 1

    def test_non_quadratic_residues(self):
        """Non-quadratic residues should return None."""
        test_cases = [
            (3, 5),
            (3, 7),
            (2, 11),
            (2, 13),
            (3, 17),
        ]

        for a, p in test_cases:
            with self.subTest(a=a, p=p):
                self.assertIsNone(tonelli_shanks(a, p))

    def test_prime_congruent_to_3_mod_4(self):
        """Test the p % 4 == 3 optimized case."""
        test_cases = [
            (4, 7),
            (3, 11),
            (9, 19),
            (16, 23),
        ]

        for a, p in test_cases:
            with self.subTest(a=a, p=p):
                root = tonelli_shanks(a, p)

                self.assertIsNotNone(root)
                self.assertEqual(pow(root, 2, p), a % p)

    def test_prime_congruent_to_1_mod_4(self):
        """Test the general Tonelli-Shanks case where p % 4 == 1."""
        test_cases = [
            (3, 13),   # 4^2 = 16 == 3 (mod 13)
            (16, 17),  # 4^2 = 16 (mod 17)
            (8, 41),   # 7^2 = 49 == 8 (mod 41)
            (8, 113),  # 11^2 = 121 == 8 (mod 113)
        ]

        for a, p in test_cases:
            with self.subTest(a=a, p=p):
                root = tonelli_shanks(a, p)

                self.assertIsNotNone(root)
                self.assertEqual(pow(root, 2, p), a % p)

    def test_roots_are_valid(self):
        """Verify that every returned root is actually a square root."""
        test_cases = [
            (1, 7),
            (2, 7),
            (4, 7),
            (5, 11),
            (9, 13),
            (10, 13),
            (25, 29),
            (36, 41),
            (49, 113),
        ]

        for a, p in test_cases:
            with self.subTest(a=a, p=p):
                root = tonelli_shanks(a, p)

                self.assertIsNotNone(root)
                self.assertEqual(pow(root, 2, p), a % p)

    def test_result_is_in_range(self):
        """A valid modular square root should be in [0, p-1]."""
        test_cases = [
            (4, 7),
            (3, 11),
            (3, 13),
            (8, 41),
            (8, 113),
        ]

        for a, p in test_cases:
            with self.subTest(a=a, p=p):
                root = tonelli_shanks(a, p)

                self.assertIsNotNone(root)
                self.assertGreaterEqual(root, 0)
                self.assertLess(root, p)

    def test_large_prime(self):
        """Test the algorithm with larger primes."""
        # 500^2 = 250000 == 49994 (mod 100003)
        root = tonelli_shanks(49994, 100003)

        self.assertIsNotNone(root)
        self.assertEqual(pow(root, 2, 100003), 49994)

    def test_negative_and_large_residues(self):
        """Inputs should be interpreted modulo p."""
        # -3 mod 7 == 4, and 2^2 == 4 mod 7
        root = tonelli_shanks(-3, 7)
        self.assertIsNotNone(root)
        self.assertEqual(pow(root, 2, 7), (-3) % 7)

        # 11 mod 7 == 4
        root = tonelli_shanks(11, 7)
        self.assertIsNotNone(root)
        self.assertEqual(pow(root, 2, 7), 11 % 7)


if __name__ == "__main__":
    unittest.main()
