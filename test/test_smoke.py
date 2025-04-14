import unittest

from solver import nsga2


class SmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        pass
    
    def test_nsga2(self):
        nsga2.main(hv_ref=[115,-600,25], NGEN=10)

