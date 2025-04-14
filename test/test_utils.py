# import unittest
# import weakref

# from simenv.utils import deref


# class DerefTest(unittest.TestCase):
#     def setUp(self) -> None:
#         # only set object support weakref
#         self.strong = {1, }
#         self.weak = weakref.ref(self.strong)

#     def test_deref_ok(self) -> None:
#         self.assertEqual(deref(self.weak), self.strong)

#     def test_deref_fail(self) -> None:
#         self.strong = {1, }
#         self.weak = weakref.ref(self.strong)
#         del self.strong
#         self.assertRaises(ValueError, deref, self.weak)
